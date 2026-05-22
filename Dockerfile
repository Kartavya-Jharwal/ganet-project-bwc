# BWC — uv + Python toolstack for DuckDB, tests, and Appwrite clients (secrets via env).
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Dependency layer (invalidates when lock changes)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash", "-lc", "uv run python -c \"print('BWC ready — try: uv run project sync-data or uv run python -m quant_monitor.main')\""]
