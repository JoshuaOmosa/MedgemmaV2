#!/usr/bin/env python3
"""Download faster-whisper weights on a CONNECTED staging machine, then copy ./models across.

    pip install huggingface_hub
    python scripts/fetch_whisper.py --size small --dest models
"""

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download

ap = argparse.ArgumentParser()
ap.add_argument("--size", default="small", help="tiny|base|small|medium|large-v3 ...")
ap.add_argument("--dest", default="models")
args = ap.parse_args()

target = Path(args.dest) / f"whisper-{args.size}"
snapshot_download(f"Systran/faster-whisper-{args.size}", local_dir=target)
print(f"Whisper weights saved to {target}")
