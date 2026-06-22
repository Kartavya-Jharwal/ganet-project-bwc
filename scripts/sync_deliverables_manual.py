"""One-off manual deliverables mirror sync (source files + manifest + index rows)."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "deliverables" / "source"
DST = ROOT / "frontend" / "deliverables" / "source"
INDEX = ROOT / "frontend" / "deliverables" / "index.html"
MANIFEST = ROOT / "frontend" / "data" / "deliverables-manifest.json"


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    for item in SRC.iterdir():
        if item.is_file():
            shutil.copy2(item, DST / item.name)

    files = sorted(p for p in DST.iterdir() if p.is_file())
    rows: list[str] = []
    manifest_files: list[dict[str, object]] = []
    for path in files:
        name = path.name
        rows.append(
            f'                <tr><td><a href="./source/{quote(name, safe="")}" download>{name}</a></td></tr>'
        )
        manifest_files.append(
            {
                "name": name,
                "size_bytes": path.stat().st_size,
                "href": f"./deliverables/source/{name}",
            }
        )

    post = next(
        (f for f in manifest_files if "Post_Mortem" in f["name"] and str(f["name"]).endswith(".pdf")),
        None,
    )
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "team": "BWC",
        "project": "BWC",
        "source_dir": "deliverables/source",
        "post_mortem_pdf": post["name"] if post else None,
        "file_count": len(manifest_files),
        "files": manifest_files,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    html = INDEX.read_text(encoding="utf-8")
    start = html.index("<tbody>")
    end = html.index("</tbody>", start) + len("</tbody>")
    new_tbody = "<tbody>\n" + "\n".join(rows) + "\n            </tbody>"
    INDEX.write_text(html[:start] + new_tbody + html[end:], encoding="utf-8")

    print(f"Synced {len(files)} files -> {DST.relative_to(ROOT)}")
    print(f"Updated {MANIFEST.relative_to(ROOT)}")
    print(f"Updated {INDEX.relative_to(ROOT)} tbody")


if __name__ == "__main__":
    main()
