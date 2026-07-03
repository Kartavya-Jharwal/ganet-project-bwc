# Interactive quant charts (static archive)

Plotly charts visualize the Team BWC desk overlay: equity curve, drawdowns, Monte Carlo fan, correlation network, and attribution. They are **static embeds** in the public site, not a live dashboard.

Charts ship on the [Adaptive Efficiency site](https://kartavya-jharwal.github.io/ganet-project-bwc/) (`#research`, `#evidence`; legacy `results.html` redirects to `#evidence`).

Rebuild chart assets locally:

```bash
uv run python scripts/build_frontend_assets.py
```

Then rebuild MkDocs if engineering pages reference updated JSON:

```bash
uv run python -m mkdocs build -f docs/mkdocs.yml --strict
```
