# Phase FINALE (The Endgame): Project Sunset & Permanent Case Study Freeze

> ⚠️ CRITICAL INSTRUCTION: UNDER NO CIRCUMSTANCES SHALL THE DATA FREEZE OR SUNSET OCCUR BEFORE MAY 1ST, 2026. ⚠️
> The backtest timeframe and exact project conditions mathematically require the final 29-day forward projection to expire. Running the export script or spinning down architectures before May 1st invalidates the forward testing.

This document outlines the final steps to wind down the live computational engines on May 1, 2026, while preserving the ecosystem perpetually as a static, interactive academic case study.

## The Strategy
The portfolio simulation has a hard cutoff, but the epistemic value of the built analytics (Monte Carlo simulations, Fama-French regressions, Brinson attribution, and bespoke Manim-animated aesthetics) must live on. We transform the live Heroku/Appwrite tracking repo into a 100% free, static historical architecture hosted via GitHub Pages.

### Endgame Implementations (scripts/export_for_archive.py)

1. **Database Freeze:**
   - Script will recursively pull all final portfolio_snapshots, telemetry logs, and signals from the Appwrite backend into standard JSON/DuckDB static files.
   - These files will be checked strictly into the repository under a frozen data namespace.

2. **Docs & UI Rendering Compilation:**
   - Convert all dynamically generated graphs, Manim mathematical simulation loops, Monte Carlo distributions, and bespoke PDF Tear Sheets into static web assets (MP4, WebM, SVG, JSON).
   - Embed these directly into the MKDocs/custom UI frameworks such that a visitor browsing the repository in the future experiences the exact site, just without "live" polling.

3. **Deactivation & Security:**
   - Disable the Appwrite live instance.
   - Cycle all Doppler API keys, broker API keys (Alpaca, FRED), and scrapers.
   - Spin down the Heroku APScheduler worker dynos.
   - Lock down the main branch.

**Conclusion:** The live telemetry ends, but the architectural proof remains perfectly preserved.
