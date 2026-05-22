# Phases 1–5: Data, features, and base models

Summary of the foundation layer (see [roadmap.md](../roadmap.md) for full task lists).

## Phase 1 — Data pipeline

Multi-source ingestion: yfinance/Massive prices, FRED macro, news, optional Appwrite persistence, DuckDB local matrix, Scrapy spiders. `DataPipeline` orchestrates fetch with cache TTLs from `config.toml`.

## Phase 2 — Feature engineering

Moving-average matrix (EMA, SMA, KAMA, VWAP, HMA), realized volatility, Hurst exponent, five-regime classifier. Sentiment preprocessing hooks (FinBERT later removed).

## Phase 3 — Technical + macro models

Technical scoring: MA crossovers, RSI, MACD, Bollinger squeeze, volume confirmation. Macro: VIX, yield curve, DXY, per-ticker impact; regimes `RISK_ON` / `TRANSITION` / `CRISIS`.

## Phase 4 — Sentiment model

**Removed** — torch/FinBERT dropped; weights redistributed to technical/macro in config.

## Phase 5 — Fundamental model

Sector-relative valuation (P/E, P/S, EV/EBITDA) and analyst revision hooks from stored fundamentals.

---

[← Phase 0](phase-00-scaffold.md) · [Phases 6–10 →](phase-06-10-core.md) · [Index](README.md)
