# Phases 6–10: Fusion through deployment

Core product loop before the topological analytics track (Phases 11–21).

## Phase 6 — Signal fusion

Regime-weighted blending of technical, fundamental, and macro scores; conflict detection; output in `[-1, 1]` per ticker.

## Phase 7 — Agent orchestrator

Turns fused signals into position targets; risk caps; trade proposals vs current book from config + journal.

## Phase 8 — Backtesting

Walk-forward engine with naive equal-weight baseline vs topological HRP path; metrics to [backtest-results.json](../backtest-results.json).

## Phase 9 — CLI + dashboard

Typer CLI (`project`), Rich terminal dashboard, optional OpenBB panels when configured.

## Phase 10 — Alerts + deployment

ntfy alerts, Scrapy/Appwrite hardening, GitHub Actions CI, GitHub Pages static site. Heroku path deprecated in favour of local/`uv` reproducibility.

---

[← Phases 1–5](phase-01-05-roadmap.md) · [Phases 11–21 →](phase-11-21-track.md) · [Index](README.md)
