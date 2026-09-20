#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: entrypoint.sh {api|worker|cleanup}" >&2
  exit 64
fi

case "$1" in
  api)
    exec /app/.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
    ;;
  worker)
    exec /app/.venv/bin/rq worker --url "$OCR_REDIS_URL" ocr
    ;;
  cleanup)
    exec /app/.venv/bin/python -m backend.app.cleanup
    ;;
  *)
    echo "usage: entrypoint.sh {api|worker|cleanup}" >&2
    exit 64
    ;;
esac
