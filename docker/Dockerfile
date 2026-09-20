# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      curl \
      libglib2.0-0 \
      libgl1 \
      libsm6 \
      libxext6 \
      tesseract-ocr \
      tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.0 /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY backend/ ./backend/
COPY evaluation/ ./evaluation/
COPY --from=frontend-build /build/frontend/dist ./frontend-dist/
COPY docker/entrypoint.sh ./docker/entrypoint.sh
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data/jobs \
    && chown -R appuser:appuser /app /data/jobs \
    && chmod +x /app/docker/entrypoint.sh

ENV OCR_FRONTEND_DIST=/app/frontend-dist \
    OCR_WORKSPACE_ROOT=/data/jobs
USER appuser
ENTRYPOINT ["/app/docker/entrypoint.sh"]
