# syntax=docker/dockerfile:1.9
ARG UV_VERSION=latest
ARG PYTHON_VERSION=3.12
ARG PYTHON_BASE=${PYTHON_VERSION}-slim

# uv stage
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# build stage
FROM python:$PYTHON_BASE AS builder
SHELL ["bash", "-e", "-x", "-o", "pipefail", "-c"]

RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    gcc \
    libc6-dev \
    libpq-dev \
    ca-certificates
EOT

COPY --from=uv /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python${PYTHON_VERSION}

WORKDIR /code
ARG ENVIRONMENT
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
  uv --version && uv sync --locked --no-install-project

# run stage
FROM python:$PYTHON_BASE
SHELL ["bash", "-e", "-x", "-o", "pipefail", "-c"]

RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    libpq5
EOT

RUN <<EOT
groupadd -r app
useradd -r -d /code -g app -N app
EOT

USER app
WORKDIR /code
ENV PATH="/code/.venv/bin:$PATH"
ENV PYTHONPATH="/code:$PYTHONPATH"
COPY --chown=app:app --from=builder /code/.venv/ .venv/
COPY --chown=app:app alembic.ini docker-cmd.sh pyproject.toml ./
COPY --chown=app:app alembic/ alembic/
COPY --chown=app:app app/ app/

RUN python -m compileall .  # compile app files

ARG ENVIRONMENT
ARG APP_NAME
ARG APP_VERSION
ARG COMMIT_SHA
ENV ENVIRONMENT=${ENVIRONMENT}
ENV APP_NAME=${APP_NAME}
ENV APP_VERSION=${APP_VERSION}
ENV COMMIT_SHA=${COMMIT_SHA}

RUN <<EOT
python -V
python -m site
python -c 'import app'
EOT

STOPSIGNAL SIGINT
CMD ["./docker-cmd.sh"]
