# syntax=docker/dockerfile:1.7
#
# Build context MUST be the repository root (the uv workspace), not this folder:
#   docker build -f jobs/account/Dockerfile -t <registry>/account:<sha> .
#
# Option B distroless: a uv-managed standalone Python is installed under a fixed
# path in the builder and copied verbatim into a distroless/cc runtime, so the
# virtual environment resolves its interpreter without a shell or activation.

############################
# Builder
############################
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON=3.11 \
    UV_PYTHON_PREFERENCE=only-managed \
    UV_PYTHON_INSTALL_DIR=/opt/python

WORKDIR /app

# 1) Dependency layer (cached): only the manifests are needed to resolve deps.
COPY pyproject.toml uv.lock ./
COPY packages/common/pyproject.toml packages/common/
COPY jobs/account/pyproject.toml jobs/account/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev --package etl-account

# 2) Project layer: install workspace packages as non-editable wheels.
COPY packages/common packages/common
COPY jobs/account jobs/account
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable --package etl-account

############################
# Runtime (distroless, no shell)
############################
FROM gcr.io/distroless/cc-debian12

# Standalone interpreter + resolved venv, copied to identical paths so the
# venv's symlinks and entry-point shebangs resolve under execve.
COPY --from=builder /opt/python /opt/python
COPY --from=builder /app/.venv /app/.venv

ENTRYPOINT ["/app/.venv/bin/account-job"]
