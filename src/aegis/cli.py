"""Command line entry point: ``aegis {watch,process,text,selfcheck}``."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from . import __version__
from .airgap import AirgapViolation, egress_possible, enforce_airgap
from .config import Settings
from .llm import LLMError, OllamaClient
from .pipeline import Pipeline, PipelineResult
from .store import write_result

log = logging.getLogger("aegis")  # NOTE: never log transcript or note content (PHI).


def _build_pipeline(s: Settings, need_audio: bool) -> Pipeline:
    transcriber = None
    if need_audio:
        from .transcribe import WhisperTranscriber

        transcriber = WhisperTranscriber(
            s.whisper_model_path, s.whisper_device, s.whisper_compute_type
        )
    check = None
    if s.use_nemo:
        from .nemo_rails import make_nemo_check

        check = make_nemo_check(s.nemo_config_dir)
    return Pipeline(
        llm=OllamaClient(s.llm_host, s.llm_model, s.llm_timeout_s),
        transcriber=transcriber,
        injection_policy=s.injection_policy,
        max_audio_seconds=s.max_audio_seconds,
        extra_input_check=check,
    )


def _guard(s: Settings) -> None:
    if s.require_airgap:
        enforce_airgap()


def _process_file(pipe: Pipeline, wav: Path, s: Settings) -> PipelineResult:
    try:
        result = pipe.process_audio(wav)
    except Exception as exc:  # noqa: BLE001 - keep the watcher alive; log type only
        result = PipelineResult(
            status="failed", source=wav.name, model=pipe.llm.model, error=type(exc).__name__
        )
    write_result(s.outbox, wav.stem, result)
    log.info("processed %s -> %s", wav.name, result.status)
    return result


def cmd_watch(s: Settings, once: bool) -> int:
    _guard(s)
    pipe = _build_pipeline(s, need_audio=True)
    pipe.llm.wait_until_ready()  # type: ignore[attr-defined]
    log.info("ready; watching %s", s.inbox)
    while True:
        for wav in sorted(s.inbox.glob("*.wav")):
            done = (s.outbox / f"{wav.stem}.soap.json").exists()
            settled = time.time() - wav.stat().st_mtime > 2  # skip files still being written
            if not done and settled:
                _process_file(pipe, wav, s)
        if once:
            return 0
        time.sleep(s.poll_interval_s)


def cmd_process(s: Settings, path: Path) -> int:
    _guard(s)
    pipe = _build_pipeline(s, need_audio=True)
    result = _process_file(pipe, path, s)
    return 0 if result.status == "ok" else 2


def cmd_text(s: Settings, path: str) -> int:
    _guard(s)
    text = sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")
    result = _build_pipeline(s, need_audio=False).process_text(text, source="text-input")
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 0 if result.status == "ok" else 2


def cmd_selfcheck(s: Settings) -> int:
    llm = OllamaClient(s.llm_host, s.llm_model)
    report = {
        "egress_blocked": not egress_possible(),
        "llm_ready": llm.is_ready(),
        "model": s.llm_model,
        "whisper_model_present": Path(s.whisper_model_path).exists(),
    }
    print(json.dumps(report))
    required = report["llm_ready"] and (report["egress_blocked"] or not s.require_airgap)
    return 0 if required else 1


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=os.getenv("AEGIS_LOG_LEVEL", "INFO"), format="%(asctime)s %(message)s"
    )
    parser = argparse.ArgumentParser(prog="aegis", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("watch", help="process WAV files dropped in the inbox")
    w.add_argument("--once", action="store_true", help="single pass, then exit")
    p = sub.add_parser("process", help="process one WAV file")
    p.add_argument("audio", type=Path)
    t = sub.add_parser("text", help="run guardrails + SOAP on a transcript (file or '-')")
    t.add_argument("transcript")
    sub.add_parser("selfcheck", help="verify air-gap and model availability")
    args = parser.parse_args(argv)

    settings = Settings.from_env()
    try:
        if args.cmd == "watch":
            return cmd_watch(settings, args.once)
        if args.cmd == "process":
            return cmd_process(settings, args.audio)
        if args.cmd == "text":
            return cmd_text(settings, args.transcript)
        return cmd_selfcheck(settings)
    except (AirgapViolation, LLMError) as exc:
        print(f"aegis: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
