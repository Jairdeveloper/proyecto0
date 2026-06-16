FROM python:3.11-slim

WORKDIR /app

COPY compiler-bot/agentic_pipeline/ /app/agentic_pipeline/
COPY compiler-bot/agentic /app/agentic
COPY VERSION /app/VERSION

RUN pip install --no-cache-dir -e /app/agentic_pipeline/

ENTRYPOINT ["python3", "/app/agentic"]
CMD ["--help"]
