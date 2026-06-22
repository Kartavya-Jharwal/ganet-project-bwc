"""Build all static frontend assets for the GitHub Pages microsite.

Orchestrates chart generation, results JSON, and tearsheet PDF into
the frontend/ directory tree. Uses PortfolioHistoryEngine for real data.

Usage:
    uv run python scripts/build_frontend_assets.py
    uv run python scripts/build_frontend_assets.py --output-dir frontend
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure project root and scripts/ are importable
_project_root = str(Path(__file__).parent.parent)
_scripts_dir = str(Path(__file__).parent)
for p in (_project_root, _scripts_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_all(output_dir: str = "frontend") -> None:
    """Generate every static asset the frontend needs."""
    root = Path(output_dir)
    charts_dir = root / "charts"
    data_dir = root / "data"
    assets_dir = root / "assets"

    for d in (charts_dir, data_dir, assets_dir):
        d.mkdir(parents=True, exist_ok=True)

    # --- 0. Initialize PortfolioHistoryEngine (real data source) ---
    engine = None
    try:
        from quant_monitor.data.portfolio_history import PortfolioHistoryEngine

        engine = PortfolioHistoryEngine()
        nav = engine.get_portfolio_nav()
        logger.info(
            "PortfolioHistoryEngine loaded: %d trading days, NAV $%s -> $%s",
            len(nav),
            f"{nav.iloc[0]:,.0f}" if len(nav) > 0 else "?",
            f"{nav.iloc[-1]:,.0f}" if len(nav) > 0 else "?",
        )
    except Exception as e:
        logger.warning("PortfolioHistoryEngine unavailable: %s -- using synthetic fallbacks", e)

    # --- 1. Plotly Charts ---
    logger.info("=== Generating Plotly charts ===")
    try:
        from generate_plotly_dashboard import generate_all_charts

        generate_all_charts(str(charts_dir))
        logger.info("Plotly charts complete -> %s", charts_dir)

        results_src = charts_dir / "results.json"
        results_dst = data_dir / "results.json"
        if results_src.exists():
            results_dst.write_text(results_src.read_text(encoding="utf-8"), encoding="utf-8")
            results_src.unlink()
            logger.info("results.json moved to %s", results_dst)
    except Exception as e:
        logger.error("Plotly chart generation failed: %s", e, exc_info=True)

    # --- 2. Behavioural audit JSON ---
    if engine is not None:
        logger.info("=== Running behavioural audit ===")
        try:
            from quant_monitor.backtest.behavioural import run_full_behavioural_audit

            trades = engine.get_trade_log()
            prices = engine._fetch_prices()
            audit = run_full_behavioural_audit(
                trades, prices, engine._initial_capital
            )
            audit_path = data_dir / "behavioural-audit.json"
            audit_path.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
            logger.info("Behavioural audit complete -> %s", audit_path)
        except Exception as e:
            logger.warning("Behavioural audit failed: %s", e)

    # --- 3. Full metrics JSON (superset of results.json) ---
    if engine is not None:
        logger.info("=== Computing full metrics ===")
        try:
            metrics = engine.compute_all_metrics()
            factor_reg = engine.run_factor_regression()
            metrics["factor_regression"] = factor_reg

            full_path = data_dir / "full-metrics.json"
            full_path.write_text(json.dumps(metrics, indent=2, default=str), encoding="utf-8")
            logger.info("Full metrics complete -> %s", full_path)
        except Exception as e:
            logger.warning("Full metrics failed: %s", e)

    # --- 4. PDF Tearsheet ---
    logger.info("=== Generating PDF tearsheet ===")
    try:
        from generate_tearsheet import generate_tearsheet

        generate_tearsheet(
            output_path=str(assets_dir / "tearsheet.pdf"),
            benchmark="SPY",
        )
        logger.info("Tearsheet complete -> %s", assets_dir / "tearsheet.pdf")
    except Exception as e:
        logger.error("Tearsheet generation failed: %s", e, exc_info=True)

    # --- 4b. Institutional PDF mirrors (methodology / report dossier) ---
    inst_pdf = Path("deliverables/source/BWC_Institutional_Tearsheet.pdf")
    if not inst_pdf.is_file():
        inst_pdf = Path("docs/BWC_Institutional_Tearsheet.pdf")
    if inst_pdf.is_file():
        for name in ("methodology.pdf", "institutional_report.pdf"):
            dest = assets_dir / name
            shutil.copy2(inst_pdf, dest)
            logger.info("Copied institutional PDF -> %s", dest)
    else:
        logger.warning("Missing %s — methodology/report PDF mirrors skipped", inst_pdf)

    # --- 5. Client post-mortem PDF (primary narrative) ---
    _copy_post_mortem_pdf(assets_dir)

    # --- 6. Copy backtest / MC JSON ---
    logger.info("=== Copying backtest & MC results ===")
    for name in ("backtest-results.json", "mc-forward-results.json"):
        src = Path("docs") / name
        dst = data_dir / name
        if src.exists():
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            logger.info("Copied %s -> %s", name, dst)
        else:
            logger.warning("Missing %s", src)

    # --- 7. Committee deliverables (BWC packet) ---
    logger.info("=== Syncing deliverables to frontend ===")
    _sync_deliverables(root)
    _write_deliverables_manifest(data_dir)
    _write_commit_log(data_dir)

    # --- 8. Excel metrics + report excerpts (one-page case study) ---
    logger.info("=== Extracting excel metrics and report excerpts ===")
    try:
        from extract_frontend_narrative_data import (  # noqa: PLC0415
            parse_excel_metrics,
            parse_report_excerpts,
            parse_sheet011_timeline,
        )

        (data_dir / "excel-metrics.json").write_text(
            json.dumps(parse_excel_metrics(), indent=2), encoding="utf-8"
        )
        (data_dir / "desk-timeline.json").write_text(
            json.dumps(parse_sheet011_timeline(), indent=2), encoding="utf-8"
        )
        (data_dir / "report-excerpts.json").write_text(
            json.dumps(parse_report_excerpts(), indent=2), encoding="utf-8"
        )
        logger.info("Narrative JSON -> %s", data_dir)
    except Exception as e:
        logger.warning("Narrative extract failed: %s", e)

    # --- 9. Open Graph social preview card ---
    logger.info("=== Building OG card ===")
    _build_og_card(assets_dir)

    logger.info("=== Build complete ===")


def _build_og_card(assets_dir: Path) -> None:
    """Rasterize a branded Open Graph card (1200×630) for social previews."""
    out = assets_dir / "og-card.png"
    if out.is_file():
        logger.info("Open Graph card already present — keeping %s", out)
        return

    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except ImportError:
        logger.warning("matplotlib unavailable — og-card.png skipped (og-card.svg remains)")
        return

    fig, ax = plt.subplots(figsize=(12, 6.3), dpi=100)
    ax.set_xlim(0, 1200)
    ax.set_ylim(0, 630)
    ax.axis("off")
    fig.patch.set_facecolor("#050505")
    ax.set_facecolor("#050505")
    ax.add_patch(Rectangle((0, 622), 1200, 8, color="#a78bfa", linewidth=0))
    ax.text(80, 430, "Team BWC", fontsize=72, color="#fafafa", fontweight="bold", va="top")
    ax.text(80, 360, "HULT IC POST-MORTEM · CHL-0200", fontsize=24, color="#a78bfa", va="top")
    ax.text(80, 250, "-4.37% desk close", fontsize=48, color="#f87171", fontweight="bold", va="top")
    ax.text(80, 180, "Apr 2 trough: -6.44% vs SPY -11.72%", fontsize=22, color="#4ade80", va="top")
    ax.text(80, 110, "Faculty score 422/430 · Static archive", fontsize=20, color="#a1a1aa", va="top")
    fig.savefig(out, facecolor="#050505", bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    logger.info("Open Graph card -> %s", out)


def _copy_post_mortem_pdf(assets_dir: Path) -> None:
    """Mirror client post-mortem PDF into frontend/assets/post-mortem.pdf."""
    candidates = [
        Path("deliverables/source/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pdf"),
        Path("deliverables/Client_Post_Mortem_Investment_Challenge-Team-5-BWC_CH200.pdf"),
    ]
    for src in candidates:
        if src.is_file():
            dest = assets_dir / "post-mortem.pdf"
            shutil.copy2(src, dest)
            logger.info("Post-mortem PDF -> %s", dest)
            return
    logger.warning("Client post-mortem PDF not found under deliverables/")


def _write_commit_log(data_dir: Path, *, limit: int = 40) -> None:
    """Write recent git commits for static footer / crawler discovery."""
    repo = "https://github.com/Kartavya-Jharwal/ganet-project-bwc"
    payload: dict[str, object] = {
        "repository": repo,
        "branch": "main",
        "commits_url": f"{repo}/commits/main",
        "index_source_url": f"{repo}/blob/main/frontend/index.html",
        "generated_at": datetime.now(UTC).isoformat(),
        "commit_count": 0,
        "commits": [],
    }
    try:
        proc = subprocess.run(
            ["git", "log", f"-n{limit}", "--format=%h|%cI|%s"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        commits: list[dict[str, str]] = []
        for line in proc.stdout.splitlines():
            if not line.strip():
                continue
            short_hash, iso_date, subject = line.split("|", 2)
            commits.append(
                {
                    "hash": short_hash,
                    "date": iso_date[:10],
                    "subject": subject.strip(),
                }
            )
        payload["commits"] = commits
        payload["commit_count"] = len(commits)
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as exc:
        logger.warning("Commit log export failed: %s", exc)

    out = data_dir / "commit-log.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Commit log -> %s (%d commits)", out, payload["commit_count"])


def _write_deliverables_manifest(data_dir: Path) -> None:
    """Write JSON manifest of committee files for static site / health checks."""
    source = Path("deliverables/source")
    if not source.is_dir():
        logger.warning("No deliverables/source — manifest skipped")
        return

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
    post_mortem = next(
        (f for f in files if "Post_Mortem" in f["name"] and f["name"].endswith(".pdf")),
        None,
    )
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "team": "BWC",
        "project": "BWC",
        "source_dir": "deliverables/source",
        "post_mortem_pdf": post_mortem["name"] if post_mortem else None,
        "file_count": len(files),
        "files": files,
    }
    out = data_dir / "deliverables-manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info("Deliverables manifest -> %s (%d files)", out, len(files))


def _sync_deliverables(frontend_root: Path) -> None:
    """Mirror deliverables/source into frontend/deliverables for GitHub Pages."""
    src_root = Path("deliverables")
    dst_root = frontend_root / "deliverables"
    source_src = src_root / "source"
    if not source_src.is_dir():
        logger.warning("No deliverables/source — skip")
        return

    dst_source = dst_root / "source"
    if dst_source.exists():
        shutil.rmtree(dst_source)
    shutil.copytree(source_src, dst_source)

    index_path = dst_root / "index.html"
    if index_path.is_file():
        logger.info(
            "Deliverables source synced -> %s (%d files); kept hand-edited %s",
            dst_source,
            len(list(dst_source.iterdir())),
            index_path.name,
        )
        return

    files = sorted(f.name for f in dst_source.iterdir() if f.is_file())
    rows = "\n".join(
        f'                <tr><td><a href="./source/{name}" download>{name}</a></td></tr>'
        for name in files
    )
    dst_root.mkdir(parents=True, exist_ok=True)
    (dst_root / "index.html").write_text(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team BWC Deliverables | Project BWC</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans&family=JetBrains+Mono&family=Space+Grotesk:wght@600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="../styles/tokens.css">
    <link rel="stylesheet" href="../styles/layout.css">
    <link rel="stylesheet" href="../styles/pages.css">
</head>
<body class="theme-dark noise-bg">
    <div class="sunset-freeze-bar text-mono" role="status">TEAM BWC · COMMITTEE DELIVERABLES · SUNSET 2026-05-01</div>
    <nav class="l-navbar">
        <a href="../index.html" class="nav-brand text-display">BWC</a>
        <div class="nav-links">
            <a href="../research.html" class="nav-link">Program</a>
            <a href="../results.html" class="nav-link">Quant telemetry</a>
            <a href="../docs/index.html" class="nav-link">Technical docs</a>
            <a href="../assets/post-mortem.pdf" class="nav-link" download>Post-mortem PDF</a>
        </div>
    </nav>
    <main class="page-content" style="max-width:900px;margin:0 auto;padding:var(--spacing-8);">
        <h1 class="text-hero">Committee deliverables</h1>
        <p class="text-muted">Primary narrative for the Hult investment program. Faculty feedback is incorporated. The quant engine is documented separately.</p>
        <table class="results-table" style="width:100%;margin-top:var(--spacing-6);">
            <thead><tr><th>File</th></tr></thead>
            <tbody>
{rows}
            </tbody>
        </table>
    </main>
</body>
</html>
""",
        encoding="utf-8",
    )
    logger.info("Deliverables synced -> %s (%d files)", dst_root, len(files))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build all frontend static assets")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="frontend",
        help="Root output directory (default: frontend)",
    )
    args = parser.parse_args()
    build_all(output_dir=args.output_dir)
