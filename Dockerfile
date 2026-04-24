FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN pip install --no-cache-dir uv

COPY app ./app
COPY docs ./docs
COPY benchmark.py ./
COPY .env.example ./

RUN uv sync --frozen --no-dev

EXPOSE 8080 8081
