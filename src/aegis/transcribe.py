"""Local speech-to-text via faster-whisper (CTranslate2). Never touches the network."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class Transcriber(Protocol):
    def transcribe(self, wav_path: Path) -> str: ...


class WhisperTranscriber:
    def __init__(self, model_path: str, device: str = "cpu", compute_type: str = "int8") -> None:
        from faster_whisper import WhisperModel  # imported lazily: heavy optional dependency

        # local_files_only guarantees no attempt to download weights at runtime.
        self._model = WhisperModel(
            model_path, device=device, compute_type=compute_type, local_files_only=True
        )

    def transcribe(self, wav_path: Path) -> str:
        segments, _info = self._model.transcribe(str(wav_path), vad_filter=True, beam_size=5)
        return " ".join(seg.text.strip() for seg in segments).strip()
