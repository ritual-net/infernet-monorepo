FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR 1
ENV RUNTIME docker
ENV PYTHONPATH src

RUN apt-get update && apt-get install -y curl

# install uv
RUN curl -LsSf https://astral.sh/uv/0.4.28/install.sh | sh
COPY requirements.lock .

ARG index_url
ENV UV_EXTRA_INDEX_URL ${index_url}

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=requirements.lock,target=requirements.lock \
    /root/.cargo/bin/uv pip install --system -r requirements.lock
