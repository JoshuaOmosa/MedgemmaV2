"""EXPERIMENTAL optional NeMo Guardrails input rail (enable with AEGIS_USE_NEMO=true).

Uses the 'self check input' flow defined in config/guardrails/. A blocked input makes the
rails return the fixed refusal string AEGIS_BLOCKED (see rails.co). Requires the ``nemo``
extra and a NeMo-compatible local model configured in config/guardrails/config.yml.
This adapter has not been validated against every nemoguardrails release; pin your version.
"""

from __future__ import annotations

from collections.abc import Callable

BLOCK_MARKER = "AEGIS_BLOCKED"


def make_nemo_check(config_dir: str) -> Callable[[str], bool]:
    from nemoguardrails import LLMRails, RailsConfig

    rails = LLMRails(RailsConfig.from_path(config_dir))

    def allowed(text: str) -> bool:
        reply = rails.generate(messages=[{"role": "user", "content": text}])
        content = reply.get("content", "") if isinstance(reply, dict) else str(reply)
        return BLOCK_MARKER not in content

    return allowed
