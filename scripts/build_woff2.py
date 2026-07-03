#!/usr/bin/env python
"""Regenerate woff2 (brotli) copies of the self-hosted variable fonts.

The public microsite (``frontend/styles/fonts.css``) serves woff2 first for a
much smaller cold-load payload and keeps the original ``.ttf`` as a fallback.
Run this whenever the ``.ttf`` sources under ``frontend/assets/fonts`` change.

    uv run python scripts/build_woff2.py
    # or, with brotli available on the system interpreter:
    python scripts/build_woff2.py

Requires ``fonttools`` and ``brotli`` (``pip install fonttools brotli``).
"""

from __future__ import annotations

from pathlib import Path

from fontTools.ttLib import TTFont

FONT_ROOT = Path(__file__).resolve().parent.parent / "frontend" / "assets" / "fonts"

# Variable fonts referenced by @font-face in frontend/styles/fonts.css.
VARIABLE_FONTS = [
    "Darker_Grotesque/DarkerGrotesque-VariableFont_wght.ttf",
    "Source_Sans_3/SourceSans3-VariableFont_wght.ttf",
    "Source_Sans_3/SourceSans3-Italic-VariableFont_wght.ttf",
    "JetBrains_Mono/JetBrainsMono-VariableFont_wght.ttf",
    "Playfair_Display/PlayfairDisplay-VariableFont_wght.ttf",
    "Playfair_Display/PlayfairDisplay-Italic-VariableFont_wght.ttf",
]


def main() -> int:
    total_src = total_dst = 0
    for rel in VARIABLE_FONTS:
        src = FONT_ROOT / rel
        if not src.exists():
            print(f"skip (missing): {rel}")
            continue
        dst = src.with_suffix(".woff2")
        font = TTFont(src)
        font.flavor = "woff2"
        font.save(dst)
        src_kb = src.stat().st_size // 1024
        dst_kb = dst.stat().st_size // 1024
        total_src += src_kb
        total_dst += dst_kb
        print(f"{dst.name:48s} {src_kb:5d}KB -> {dst_kb:5d}KB")
    if total_src:
        pct = round(100 * (1 - total_dst / total_src))
        print(f"{'total':48s} {total_src:5d}KB -> {total_dst:5d}KB ({pct}% smaller)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
