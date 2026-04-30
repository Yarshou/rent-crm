# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.13
ARG POETRY_VERSION=2.3.1
ARG APP_UID=1000
ARG APP_GID=1000


FROM python:${PYTHON_VERSION}-slim AS builder

ARG POETRY_VERSION

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=10 \
    POETRY_VERSION=${POETRY_VERSION} \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_CACHE_DIR=/tmp/poetry-cache \
    POETRY_REQUESTS_TIMEOUT=120

#RUN apt-get update \
#    && apt-get install -y --no-install-recommends build-essential \
#    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    --mount=type=cache,target=/tmp/poetry-cache,sharing=locked \
    poetry install --only main --no-root


FROM python:${PYTHON_VERSION}-slim AS runtime

ARG APP_UID
ARG APP_GID

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH=/app/app \
    APP_PORT=8000 \
    APP_WORKERS=4

RUN groupadd --system --gid "${APP_GID}" app \
    && useradd --system --uid "${APP_UID}" --gid app \
        --home-dir /home/app --create-home --shell /sbin/nologin app

WORKDIR /app

COPY --from=builder --chown=app:app /app/.venv ./.venv
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app app ./app

USER app

EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn config.app:app -k uvicorn.workers.UvicornWorker -w \"${APP_WORKERS}\" -b \"0.0.0.0:${APP_PORT}\""]
