"""Verify microsite copy avoids em dashes and semicolons in user-facing prose."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

EM_DASH = "\u2014"

COPY_FILES = [
    FRONTEND / "index.html",
    FRONTEND / "llms.txt",
    FRONTEND / "data" / "site-summary.json",
    FRONTEND / "data" / "behavioural-audit.json",
    FRONTEND / "data" / "desk-timeline.json",
    FRONTEND / "data" / "report-excerpts.json",
    FRONTEND / "data" / "deliverables-manifest.json",
    FRONTEND / "research.html",
    FRONTEND / "results.html",
    FRONTEND / "story.html",
    FRONTEND / "robots.txt",
    FRONTEND / "README.md",
]


def collect_json_strings(obj: object) -> list[str]:
    out: list[str] = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out.extend(collect_json_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(collect_json_strings(v))
    return out


def normalize_prose(text: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-zA-Z0-9#]+;", " ", text)
    return text


def check_text(label: str, text: str, errors: list[str]) -> None:
    prose = normalize_prose(text) if "<" in text else text
    if EM_DASH in prose:
        snippet = prose[prose.index(EM_DASH) - 20 : prose.index(EM_DASH) + 20].replace("\n", " ")
        errors.append(f"{label}: em dash near …{snippet}…")
    if ";" in prose:
        snippet = prose[prose.index(";") - 20 : prose.index(";") + 20].replace("\n", " ")
        errors.append(f"{label}: semicolon near …{snippet}…")


def check_main_js_user_strings(errors: list[str]) -> None:
    path = FRONTEND / "js" / "main.js"
    if not path.is_file():
        errors.append("main.js: missing")
        return
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"title:\s*'([^']*)'", text):
        chunk = match.group(1)
        if ";" in chunk or EM_DASH in chunk:
            errors.append(f"main.js title: {chunk[:80]!r}")
    for match in re.finditer(
        r"\$\{data\.word_count[^`]*\} — pull quotes below; full HTM is authoritative\.",
        text,
    ):
        errors.append("main.js memo excerpt intro still uses forbidden punctuation")
    if "return '—'" in text or 'return "—"' in text:
        errors.append("main.js: em dash null placeholder (use n/a)")


def verify_frontend_copy() -> bool:
    errors: list[str] = []

    for path in COPY_FILES:
        if not path.is_file():
            errors.append(f"missing copy file: {path.relative_to(ROOT)}")
            continue
        raw = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            check_text(str(path.relative_to(ROOT)), raw, errors)
        elif path.suffix == ".json":
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                errors.append(f"{path.name}: invalid JSON ({e})")
                continue
            for i, s in enumerate(collect_json_strings(data)):
                check_text(f"{path.name} string #{i + 1}", s, errors)
        else:
            check_text(str(path.relative_to(ROOT)), raw, errors)

    check_main_js_user_strings(errors)

    if errors:
        for err in errors:
            print(f"frontend copy: {err}", file=sys.stderr)
        return False
    return True


def main() -> int:
    return 0 if verify_frontend_copy() else 1


if __name__ == "__main__":
    raise SystemExit(main())
