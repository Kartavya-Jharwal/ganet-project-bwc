# Sunset freeze — local build & verify (Windows)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "==> Sync environment"
uv sync --frozen

Write-Host "==> DuckDB prep"
uv run python scripts/prep_duckdb_and_sync.py
uv run python scripts/clean_duckdb_prices.py

Write-Host "==> Tests"
uv run python -m pytest tests/ -m "not integration" -q

Write-Host "==> Frontend assets"
uv run python scripts/build_frontend_assets.py

Write-Host "==> MkDocs (strict)"
uv run python -m mkdocs build -f docs/mkdocs.yml --strict

Write-Host "==> Docs export"
try { uv run python scripts/export_for_archive.py } catch { Write-Host "export skipped: $_" }

Write-Host "==> Repo health"
uv run python scripts/verify_repo_health.py --strict-artifacts

Write-Host "==> Done. Open frontend/index.html"
