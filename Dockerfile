FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml ./
RUN uv sync --no-dev --no-install-project

COPY . .
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:${PATH}"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
