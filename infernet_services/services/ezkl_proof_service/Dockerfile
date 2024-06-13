FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR 1
ENV RUNTIME docker
ENV PYTHONPATH src
ARG index_url
ENV UV_EXTRA_INDEX_URL ${index_url}

RUN apt-get update
RUN apt-get install -y git curl

# install uv
RUN curl -LsSf https://astral.sh/uv/0.2.1/install.sh | sh
COPY requirements.txt .

# Using docker's ssh-forwarding to install private packages from github. Refer to the
# following links for more information:
# https://medium.com/@tonistiigi/build-secrets-and-ssh-forwarding-in-docker-18-09-ae8161d066
# https://stackoverflow.com/questions/43418188/ssh-agent-forwarding-during-docker-build/53548076#53548076
RUN /root/.cargo/bin/uv pip install --system --no-cache -r requirements.txt --verbose

COPY src src

ENTRYPOINT ["hypercorn", "app:create_app()"]
CMD ["-b", "0.0.0.0:3000"]
