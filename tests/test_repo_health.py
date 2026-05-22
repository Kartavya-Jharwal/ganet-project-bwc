"""Tests for scripts/verify_repo_health.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VERIFY = ROOT / "scripts" / "verify_repo_health.py"


def test_verify_repo_health_passes():
    """Smoke test: current repo satisfies sunset health checks."""
    result = subprocess.run(
        [sys.executable, str(VERIFY)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_main_js_forbidden_tokens():
    main_js = (ROOT / "frontend" / "js" / "main.js").read_text(encoding="utf-8")
    assert "FALLBACK_DATA" not in main_js
    assert "bwc-quant-live" not in main_js


def test_deliverables_manifest_valid():
    path = ROOT / "frontend" / "data" / "deliverables-manifest.json"
    if not path.is_file():
        pytest.skip("manifest not built yet — run build_frontend_assets")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data.get("files")
    assert "post_mortem_pdf" in data
