#!/usr/bin/env python3
"""Git --msg-filter helper: strip Cursor co-author / made-with trailers from commit messages."""
from __future__ import annotations

import sys

DROP = {
    "Co-authored-by: Cursor <cursoragent@cursor.com>",
    "Made-with: Cursor",
}


def main() -> None:
    lines = sys.stdin.read().splitlines()
    kept = [line for line in lines if line.strip() not in DROP]
    while kept and not kept[-1].strip():
        kept.pop()
    sys.stdout.write("\n".join(kept))
    if kept:
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
