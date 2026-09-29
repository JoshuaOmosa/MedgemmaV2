#!/usr/bin/env bash
set -euo pipefail
# Ollama binds to loopback only (OLLAMA_HOST). Its log goes to tmpfs, not to stdout.
ollama serve >/tmp/ollama.log 2>&1 &
exec aegis "$@"
