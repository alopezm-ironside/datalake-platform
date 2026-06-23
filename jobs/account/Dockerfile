# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
  UV_LINK_MODE=copy \
  UV_PYTHON=3.11 \
  UV_PYTHON_PREFERENCE=only-managed \
  UV_PYTHON_INSTALL_DIR=/opt/python

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/common/pyproject.toml packages/common/
COPY jobs/account/pyproject.toml jobs/account/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-install-project --no-dev --package etl-account

COPY packages/common packages/common
COPY jobs/account jobs/account
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --locked --no-dev --no-editable --package etl-account

FROM gcr.io/distroless/cc-debian12:nonroot@sha256:b0ae8e989418b458e0f25489bc3be523718938a2b70864cc0f6a00af1ddbd985

COPY --from=builder /opt/python /opt/python
COPY --from=builder /app/.venv /app/.venv

ENTRYPOINT ["/app/.venv/bin/account-job"]
