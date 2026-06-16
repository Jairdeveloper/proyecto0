#!/usr/bin/env bash
# docker-entrypoint.sh — Wrapper for `docker run recpl "crea modulo"`
# If args don't start with `--`, treat them as the prompt.
set -u

if [ $# -eq 0 ]; then
    exec python3 /app/agentic --help
fi

if [[ "$1" == --* ]]; then
    exec python3 /app/agentic "$@"
fi

exec python3 /app/agentic --prompt "$@"
