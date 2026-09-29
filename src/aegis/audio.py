"""Input validation for audio files. Only uncompressed PCM WAV is accepted."""

from __future__ import annotations

import wave
from pathlib import Path


class AudioError(ValueError):
    """Raised for unreadable, oversized, or unsupported audio."""


def validate_wav(path: Path, max_seconds: int) -> float:
    """Return duration in seconds, or raise AudioError."""
    try:
        with wave.open(str(path), "rb") as w:
            if w.getcomptype() != "NONE":
                raise AudioError("compressed_wav_not_supported")
            frames, rate = w.getnframes(), w.getframerate()
            if rate <= 0 or frames <= 0:
                raise AudioError("empty_audio")
            duration = frames / rate
    except (wave.Error, EOFError) as exc:
        raise AudioError("not_a_valid_pcm_wav") from exc
    if duration > max_seconds:
        raise AudioError("audio_too_long")
    return duration
