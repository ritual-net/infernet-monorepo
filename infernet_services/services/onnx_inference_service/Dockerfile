FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR 1
ENV RUNTIME docker
ENV PYTHONPATH src

ENV UV_HTTP_TIMEOUT 600

RUN apt-get update
RUN apt-get install -y git curl

# install uv
RUN curl -LsSf https://astral.sh/uv/0.2.33/install.sh | sh
COPY requirements.lock .


ARG index_url
ENV UV_EXTRA_INDEX_URL ${index_url}

# Using docker's ssh-forwarding to install private packages from github. Refer to the
# following links for more information:
# https://medium.com/@tonistiigi/build-secrets-and-ssh-forwarding-in-docker-18-09-ae8161d066
# https://stackoverflow.com/questions/43418188/ssh-agent-forwarding-during-docker-build/53548076#53548076
RUN --mount=type=ssh /root/.cargo/bin/uv pip install --system --no-cache -r requirements.lock

COPY src src

ENTRYPOINT ["python", "src/app.py"]
