"""Chronological ordering for Team BWC filed deliverables."""

from __future__ import annotations

import re
from pathlib import Path

_TRADING_LOG_RE = re.compile(r"Trading_Log-(\d+)", re.IGNORECASE)


def deliverables_sort_key(path: Path) -> tuple[int, int, str]:
    """Return a sort key that orders artifacts by simulation timeline."""
    name = path.name
    lower = name.lower()

    if "charter" in lower:
        return (0, 0, name)
    if "initial portfolio" in lower:
        return (10, 0, name)
    if "strategy synopsis" in lower:
        return (20, 0, name)
    if name.startswith("(Case Study)"):
        return (30, 0, name)
    if name.startswith("(Case)"):
        return (35, 0, name)
    if "ai advice" in lower:
        return (40, 0, name)

    log_match = _TRADING_LOG_RE.search(name)
    if log_match:
        log_num = int(log_match.group(1))
        variant = 0
        if name.endswith(".xlsx"):
            variant = 0
        elif name.endswith(".csv") and "(4)" not in name:
            variant = 1
        elif "(4)" in name:
            variant = 2
        return (50 + log_num, variant, name)

    if "esg" in lower and "mid simulation" in lower:
        return (70, 0, name)
    if "memo" in lower and "investment-chl" in lower:
        return (80, 0, name)
    if "investment-chl" in lower:
        return (85, 0, name)
    if "final excel" in lower:
        return (90, 0, name)
    if "tearsheet" in lower:
        return (100, 0, name)
    if "different format" in lower or "transaction history" in lower:
        return (110, 0, name)
    if "post_mortem" in lower:
        suffix = 0 if name.endswith(".pdf") else 1
        return (200, suffix, name)

    # Unknown files: fall back to filesystem mtime, then name.
    return (150, int(path.stat().st_mtime), name)


def sort_deliverable_paths(paths: list[Path]) -> list[Path]:
    return sorted(paths, key=deliverables_sort_key)
