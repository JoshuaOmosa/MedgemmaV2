"""Owner-only, atomic result writes."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .pipeline import PipelineResult


def write_result(outbox: Path, stem: str, result: PipelineResult) -> Path:
    outbox.mkdir(parents=True, exist_ok=True)
    final = outbox / f"{stem}.soap.json"
    tmp = outbox / f".{stem}.soap.json.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(result.to_dict(), fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, final)
    return final
