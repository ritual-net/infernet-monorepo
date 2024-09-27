FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR 1
ENV RUNTIME docker
ENV PYTHONPATH src

RUN apt-get update
RUN apt-get install -y git curl

# install uv
RUN curl -LsSf https://astral.sh/uv/0.2.33/install.sh | sh
COPY requirements.lock .

ARG index_url
ENV UV_HTTP_TIMEOUT 600
ENV UV_EXTRA_INDEX_URL ${index_url}

RUN /root/.cargo/bin/uv pip install --system --no-cache -r requirements.lock

COPY src src

ENTRYPOINT ["gunicorn", "app:create_app()"]
CMD ["-b", "0.0.0.0:3000"]
