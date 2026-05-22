#!/usr/bin/env bash
# Sunset freeze — local build & verify (POSIX). On Windows use sunset_freeze.ps1
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> Sync environment"
uv sync --frozen

echo "==> DuckDB prep"
uv run python scripts/prep_duckdb_and_sync.py
uv run python scripts/clean_duckdb_prices.py

echo "==> Tests"
uv run python -m pytest tests/ -m "not integration" -q

echo "==> Frontend assets"
uv run python scripts/build_frontend_assets.py

echo "==> MkDocs (strict)"
uv run python -m mkdocs build -f docs/mkdocs.yml --strict

echo "==> Docs export (skip if before sunset_date guard triggers)"
uv run python scripts/export_for_archive.py || true

echo "==> Repo health"
uv run python scripts/verify_repo_health.py --strict-artifacts

echo "==> Done. Open frontend/index.html and frontend/docs/"
