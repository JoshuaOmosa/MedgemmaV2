# Single container: app + Ollama on loopback. Required because `network_mode: none`
# removes all container-to-container networking, so the LLM must live in the same container.
# Build needs internet (base image, apt, pip). RUN needs none.
FROM ollama/ollama:latest

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/venv \
 && useradd -m -u 10001 aegis

ENV PATH=/opt/venv/bin:$PATH
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY config ./config
RUN pip install --no-cache-dir ".[whisper]"

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh

USER aegis
ENV HOME=/home/aegis \
    OLLAMA_HOST=127.0.0.1:11434 \
    OLLAMA_MODELS=/models \
    OLLAMA_NOPRUNE=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HF_HUB_DISABLE_TELEMETRY=1 \
    DO_NOT_TRACK=1 \
    ANONYMIZED_TELEMETRY=False \
    PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["watch"]
