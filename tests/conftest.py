import re
import struct
import wave
from pathlib import Path

import pytest

GOOD = (
    '{"subjective":"Cough for 3 days.","objective":"Afebrile.",'
    '"assessment":"Likely viral URI.","plan":"Rest and fluids."}'
)


class FakeLLM:
    model = "fake-medgemma"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate(self, system, user):
        self.calls.append((system, user))
        reply = self.replies.pop(0) if self.replies else GOOD
        return reply(system) if callable(reply) else reply


class FakeTranscriber:
    def __init__(self, text):
        self.text = text

    def transcribe(self, wav_path):
        return self.text


@pytest.fixture
def wav_file(tmp_path: Path) -> Path:
    path = tmp_path / "visit-001.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<h", 0) * 16000)  # 1 s of silence
    return path


def extract_canary(system: str) -> str:
    return re.search(r"AEGIS-CANARY-[0-9a-f]+", system).group(0)
