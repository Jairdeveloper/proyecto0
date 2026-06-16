FROM python:3.11-slim

WORKDIR /app

COPY compiler-bot/agentic_pipeline/ /app/agentic_pipeline/
COPY compiler-bot/agentic /app/agentic
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
COPY VERSION /app/VERSION

RUN pip install --no-cache-dir -e /app/agentic_pipeline/ && \
    chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
