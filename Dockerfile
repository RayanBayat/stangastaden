FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Install deps first (cached layer, busted only when lockfile or pyproject changes).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev --no-install-project

# Install the project itself.
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


FROM python:3.13-slim

# Lambda Web Adapter: runtime extension that runs our HTTP server inside
# Lambda and bridges Function URL invocations to local HTTP calls.
# https://github.com/awslabs/aws-lambda-web-adapter
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.0 /lambda-adapter /opt/extensions/lambda-adapter

ENV AWS_LWA_PORT=8000
ENV AWS_LWA_INVOKE_MODE=buffered
ENV AWS_LWA_READINESS_CHECK_PROTOCOL=tcp
ENV AWS_LWA_ASYNC_INIT=true
ENV PORT=8000

COPY --from=builder /app /app
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

CMD ["stangastaden-server"]
