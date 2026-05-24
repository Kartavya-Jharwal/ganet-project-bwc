"""Repository health checks for sunset seal and CI.

Validates archive layout, static frontend artifacts, and hygiene rules
(no legacy CLI, no FALLBACK_DATA in main.js).

Usage:
    uv run python scripts/verify_repo_health.py
    uv run python scripts/verify_repo_health.py --require-clean-git
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_PATHS = [
    "deliverables/source",
    "deliverables/README.md",
    "frontend/index.html",
    "docs/backtest-results.json",
    "docs/mc-forward-results.json",
    "docs/archive/README.md",
    "REVIEWERS.md",
    "scripts/sunset_freeze.ps1",
    "scripts/build_frontend_assets.py",
]

ARTIFACT_PATHS = [
    "frontend/assets/post-mortem.pdf",
    "frontend/data/deliverables-manifest.json",
]

OPTIONAL_ARTIFACTS = [
    "frontend/data/results.json",
]

FORBIDDEN_PATHS = [
    "quant_monitor/cli_old.py",
    "BWC",
]

MAIN_JS_FORBIDDEN = ("FALLBACK_DATA", "bwc-quant-live", "label.textContent = 'LIVE'")


def _fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)


def bootstrap_static_artifacts() -> bool:
    """Ensure post-mortem PDF and deliverables manifest exist (CI-friendly)."""
    import json
    import shutil
    from datetime import UTC, datetime

    ok = True
    assets = ROOT / "frontend" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    post_mortem = assets / "post-mortem.pdf"
    if not post_mortem.is_file():
        src = ROOT / "deliverables/source/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pdf"
        if src.is_file():
            shutil.copy2(src, post_mortem)
            print("OK: bootstrapped post-mortem.pdf")
        else:
            _fail("post-mortem.pdf missing and no source PDF in deliverables/source")
            ok = False

    manifest_path = ROOT / "frontend" / "data" / "deliverables-manifest.json"
    source = ROOT / "deliverables" / "source"
    if not manifest_path.is_file() and source.is_dir():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        files = sorted(
            (
                {
                    "name": p.name,
                    "size_bytes": p.stat().st_size,
                    "href": f"./deliverables/source/{p.name}",
                }
                for p in source.iterdir()
                if p.is_file()
            ),
            key=lambda row: row["name"],
        )
        post = next(
            (f for f in files if "Post_Mortem" in f["name"] and f["name"].endswith(".pdf")),
            None,
        )
        manifest_path.write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "team": "BWC",
                    "project": "BWC",
                    "source_dir": "deliverables/source",
                    "post_mortem_pdf": post["name"] if post else None,
                    "file_count": len(files),
                    "files": files,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print("OK: bootstrapped deliverables-manifest.json")

    return ok


def check_paths() -> bool:
    ok = True
    for rel in REQUIRED_PATHS:
        path = ROOT / rel
        if not path.exists():
            _fail(f"missing required path: {rel}")
            ok = False
    for rel in ARTIFACT_PATHS:
        path = ROOT / rel
        if not path.exists():
            _fail(f"missing static artifact: {rel} (run build_frontend_assets)")
            ok = False
    return ok


def check_optional_artifacts(*, strict: bool) -> bool:
    ok = True
    for rel in OPTIONAL_ARTIFACTS:
        path = ROOT / rel
        if not path.exists():
            msg = f"missing optional artifact: {rel}"
            if strict:
                _fail(msg)
                ok = False
            else:
                print(f"WARN: {msg}")
    return ok


def check_forbidden_paths() -> bool:
    ok = True
    for rel in FORBIDDEN_PATHS:
        path = ROOT / rel
        if path.exists():
            _fail(f"forbidden path still present: {rel}")
            ok = False
    return ok


def check_main_js() -> bool:
    main_js = ROOT / "frontend" / "js" / "main.js"
    if not main_js.is_file():
        _fail("frontend/js/main.js missing")
        return False
    text = main_js.read_text(encoding="utf-8")
    ok = True
    for needle in MAIN_JS_FORBIDDEN:
        if needle in text:
            _fail(f"main.js contains forbidden token: {needle!r}")
            ok = False
    if "STATIC ARCHIVE" not in text:
        _fail("main.js must default status label to STATIC ARCHIVE")
        ok = False
    return ok


def check_deliverables_manifest() -> bool:
    manifest_path = ROOT / "frontend" / "data" / "deliverables-manifest.json"
    if not manifest_path.is_file():
        _fail("deliverables-manifest.json missing (run build_frontend_assets)")
        return False
    try:
        import json

        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fail(f"invalid deliverables-manifest.json: {e}")
        return False
    if not data.get("files"):
        _fail("deliverables-manifest.json has empty files list")
        return False
    return True


def check_clean_git() -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        _fail("git status failed (not a git repo?)")
        return False
    dirty = result.stdout.strip()
    if dirty:
        _fail("working tree is not clean — commit or stash before sunset seal")
        for line in dirty.splitlines()[:20]:
            print(f"  {line}", file=sys.stderr)
        if len(dirty.splitlines()) > 20:
            print("  ...", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify repo health for sunset seal")
    parser.add_argument(
        "--require-clean-git",
        action="store_true",
        help="Fail if git working tree has uncommitted changes",
    )
    parser.add_argument(
        "--strict-artifacts",
        action="store_true",
        help="Require frontend/data/results.json (after full build_frontend_assets)",
    )
    args = parser.parse_args()

    checks = [
        ("bootstrap-artifacts", bootstrap_static_artifacts),
        ("paths", check_paths),
        ("optional-artifacts", lambda: check_optional_artifacts(strict=args.strict_artifacts)),
        ("main.js", check_main_js),
        ("deliverables-manifest", check_deliverables_manifest),
        ("forbidden-paths", check_forbidden_paths),
    ]
    if args.require_clean_git:
        checks.append(("clean-git", check_clean_git))

    all_ok = True
    for name, fn in checks:
        if not fn():
            all_ok = False
        else:
            print(f"OK: {name}")

    if all_ok:
        print("Repo health: PASS")
        return 0
    print("Repo health: FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
