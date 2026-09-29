import pytest

from aegis import airgap
from aegis.audio import AudioError, validate_wav
from aegis.llm import LLMError, OllamaClient


@pytest.mark.parametrize(
    "host", ["http://127.0.0.1:11434", "http://localhost:11434", "http://[::1]:11434"]
)
def test_loopback_hosts_allowed(host):
    OllamaClient(host, "m")


@pytest.mark.parametrize(
    "host", ["http://10.0.0.5:11434", "https://api.example.com", "http://ollama:11434"]
)
def test_non_loopback_hosts_rejected(host):
    with pytest.raises(LLMError):
        OllamaClient(host, "m")


def test_airgap_violation_detected(monkeypatch):
    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(airgap.socket, "create_connection", lambda *a, **k: Conn())
    with pytest.raises(airgap.AirgapViolation):
        airgap.enforce_airgap()


def test_airgap_ok_when_unreachable(monkeypatch):
    def boom(*a, **k):
        raise OSError("Network is unreachable")

    monkeypatch.setattr(airgap.socket, "create_connection", boom)
    airgap.enforce_airgap()


def test_audio_validation(wav_file):
    assert validate_wav(wav_file, 10) == pytest.approx(1.0)
    with pytest.raises(AudioError, match="audio_too_long"):
        validate_wav(wav_file, 0)
