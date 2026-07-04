"""Normalize frontend/viz_output Plotly HTML for iframe embeds.

Applies the same full-bleed layout and purple scrollbar tokens as charts/*.html.
"""

from __future__ import annotations

import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from generate_plotly_dashboard import _normalize_chart_html

_ROOT = _scripts_dir.parent

VIZ_DIR = _ROOT / "frontend" / "viz_output"


def normalize_viz_output_dir(viz_dir: Path = VIZ_DIR) -> int:
    count = 0
    for path in sorted(viz_dir.glob("*.html")):
        original = path.read_text(encoding="utf-8")
        normalized = _normalize_chart_html(original)
        if normalized != original:
            path.write_text(normalized, encoding="utf-8")
            count += 1
    return count


if __name__ == "__main__":
    updated = normalize_viz_output_dir()
    print(f"Normalized {updated} viz_output HTML file(s) in {VIZ_DIR}")
