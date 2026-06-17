"""Chart Generation Library for BWC Frontend Microsite.

Produces individual embeddable Plotly HTML chart files, each self-contained
with the Plotly CDN and styled with the institutional dark theme.

Usage:
    uv run python scripts/generate_plotly_dashboard.py [--output-dir frontend/charts]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quant_monitor.config import cfg

logger = logging.getLogger(__name__)

_MC_DAYS = cfg.mc_forward_days

COLORS = {
    "bg": "#050505",
    "paper": "#0a0a0a",
    "text": "#f4f4f5",
    "accent": "#a78bfa",
    "positive": "#00ff88",
    "negative": "#ff3366",
    "muted": "#52525b",
    "blue": "#3b82f6",
    "purple": "#8b5cf6",
}

_PLOTLY_CDN = "cdn"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _base_layout(**overrides) -> dict:
    """Return the common dark-theme layout dict."""
    layout = dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"], family="Inter, system-ui, sans-serif", size=12),
        margin=dict(t=60, b=50, l=60, r=30),
        autosize=True,
        legend=dict(bgcolor="rgba(0,0,0,0.4)", font=dict(size=10)),
    )
    layout.update(overrides)
    return layout


_CHART_EMBED_STYLE = """<style>
html,body{margin:0;padding:0;height:100%;overflow:hidden;background:#050505}
body>div{display:flex;flex-direction:column;flex:1;min-height:0;height:100%}
.plotly-graph-div{width:100%!important;height:100%!important;min-height:0!important}
</style>"""


def _normalize_chart_html(html: str) -> str:
    """Make self-contained Plotly embeds fill the iframe without internal scrollbars."""
    if _CHART_EMBED_STYLE not in html and "</head>" in html:
        html = html.replace("</head>", f"{_CHART_EMBED_STYLE}</head>", 1)
    elif _CHART_EMBED_STYLE not in html and "<body>" in html:
        html = html.replace("<body>", f"<body>{_CHART_EMBED_STYLE}", 1)

    html = re.sub(
        r'(<div[^>]*class="plotly-graph-div"[^>]*style=")height:\d+px;\s*width:100%;(")',
        r"\1height:100%;width:100%;\2",
        html,
    )
    return html


def _write_chart(fig: go.Figure, output_dir: Path, filename: str) -> Path:
    """Write a figure to a self-contained HTML file and return the path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    fig.update_layout(height=None)
    fig.write_html(
        str(path),
        include_plotlyjs=_PLOTLY_CDN,
        full_html=True,
        config=dict(
            displayModeBar=True,
            displaylogo=False,
            modeBarButtonsToRemove=["lasso2d", "select2d"],
            responsive=True,
        ),
    )
    path.write_text(_normalize_chart_html(path.read_text(encoding="utf-8")), encoding="utf-8")
    logger.info("Chart written → %s", path)
    return path


def _generate_synthetic_returns(n_days: int = 504) -> pd.Series:
    """Generate synthetic daily returns for demonstration."""
    rng = np.random.default_rng(42)
    returns = rng.normal(0.0004, 0.012, n_days)
    returns[200:230] = rng.normal(-0.008, 0.02, 30)
    returns[230:260] = rng.normal(0.005, 0.015, 30)
    dates = pd.bdate_range(end=pd.Timestamp.now(), periods=n_days)
    return pd.Series(returns, index=dates, name="daily_returns")


def _get_engine():
    """Lazily instantiate PortfolioHistoryEngine, or return None on failure."""
    try:
        from quant_monitor.data.portfolio_history import PortfolioHistoryEngine
        return PortfolioHistoryEngine()
    except Exception as exc:
        logger.warning("PortfolioHistoryEngine unavailable: %s", exc)
        return None


def _load_desk_timeline() -> dict | None:
    """Load frozen Hult desk timeline (sheet011) when present."""
    for path in (
        Path("frontend/data/desk-timeline.json"),
        Path(__file__).resolve().parent.parent / "frontend/data/desk-timeline.json",
    ):
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("series", {}).get("dates"):
                    logger.info("Loaded desk timeline from %s", path)
                    return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Desk timeline unreadable at %s: %s", path, exc)
    return None


def _desk_returns_series() -> pd.Series | None:
    """Daily returns from interpolated Hult desk NAV (Feb 02 – Apr 11 2026)."""
    desk = _load_desk_timeline()
    if desk is None:
        return None
    series = desk["series"]
    idx = pd.to_datetime(series["dates"])
    returns = pd.Series(series["daily_returns"], index=idx, name="daily_returns")
    return returns


def _get_real_returns() -> pd.Series:
    """Prefer Hult desk freeze; else quant engine; else synthetic."""
    desk_returns = _desk_returns_series()
    if desk_returns is not None and not desk_returns.empty:
        logger.info("Using HULT desk returns (%d days)", len(desk_returns))
        return desk_returns

    engine = _get_engine()
    if engine is not None:
        try:
            returns = engine.get_daily_returns()
            if returns is not None and not returns.empty:
                logger.info("Using REAL portfolio returns (%d days)", len(returns))
                return returns
        except Exception as exc:
            logger.warning("Real returns failed: %s — falling back to synthetic", exc)
    return _generate_synthetic_returns()


def _compute_drawdown(returns: pd.Series) -> pd.Series:
    cum = (1 + returns).cumprod()
    peak = cum.cummax()
    return ((peak - cum) / peak).rename("drawdown")


def _cornish_fisher_var(returns: np.ndarray, alpha: float = 0.05) -> float:
    """Cornish-Fisher expansion VaR at the given confidence level."""
    mu = np.mean(returns)
    sigma = np.std(returns, ddof=1)
    s = pd.Series(returns).skew()
    k = pd.Series(returns).kurtosis()
    z = -1.6449  # norm.ppf(0.05)
    z_cf = z + (z**2 - 1) * s / 6 + (z**3 - 3 * z) * k / 24 - (2 * z**3 - 5 * z) * s**2 / 36
    return mu + z_cf * sigma


# ---------------------------------------------------------------------------
# Individual chart generators
# ---------------------------------------------------------------------------

def generate_desk_performance(output_dir: Path) -> Path | None:
    """Portfolio vs SPY cumulative return (Hult desk freeze) -> desk-performance.html."""
    desk = _load_desk_timeline()
    if desk is None:
        logger.warning("desk-performance skipped — no desk-timeline.json")
        return None

    series = desk["series"]
    dates = pd.to_datetime(series["dates"])
    port_pct = series["portfolio_return_pct"]
    spy_pct = series["spy_return_pct"]
    ann = desk.get("annotations", {})
    phases = desk.get("phases", [])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=port_pct,
        mode="lines", name="Team 5 Portfolio",
        line=dict(color=COLORS["blue"], width=2.5),
        hovertemplate="%{x|%b %d}<br>%{y:.2f}%<extra>Portfolio</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=dates, y=spy_pct,
        mode="lines", name="SPY Benchmark",
        line=dict(color=COLORS["negative"], width=2, dash="dash"),
        hovertemplate="%{x|%b %d}<br>%{y:.2f}%<extra>SPY</extra>",
    ))

    for phase in phases:
        fig.add_vrect(
            x0=phase["start"], x1=phase["end"],
            fillcolor="rgba(59,130,246,0.06)",
            line_width=0,
            annotation_text=phase["label"],
            annotation_position="top left",
            annotation=dict(font=dict(size=9, color=COLORS["muted"])),
        )

    start = ann.get("start", {})
    trough = ann.get("trough", {})
    close = ann.get("close", {})
    if start.get("date"):
        fig.add_annotation(
            x=start["date"], y=0,
            text=start.get("label", "$1,000,000 start"),
            showarrow=True, arrowhead=2, ay=-40,
            font=dict(size=10, color=COLORS["text"]),
        )
    if trough.get("date"):
        fig.add_annotation(
            x=trough["date"],
            y=trough.get("portfolio_return_pct", 0),
            text=(
                f"Trough: Portfolio {trough.get('portfolio_return_pct', 0):.2f}% "
                f"vs SPY {trough.get('spy_return_pct', 0):.2f}% "
                f"(max DD {trough.get('max_drawdown_pct', 0):.2f}%)"
            ),
            showarrow=True, arrowhead=2, ay=30,
            font=dict(size=9, color=COLORS["muted"]),
        )
    if close.get("date"):
        nav = close.get("portfolio_nav", 0)
        fig.add_annotation(
            x=close["date"], y=close.get("portfolio_return_pct", 0),
            text=f"${nav:,.0f} close",
            showarrow=True, arrowhead=2, ay=-35,
            font=dict(size=10, color=COLORS["text"]),
        )

    t0 = dates.min().strftime("%b %d")
    t1 = dates.max().strftime("%b %d %Y")
    port_final = desk.get("portfolio_return_pct", port_pct[-1])
    spy_final = desk.get("benchmark_return_pct", spy_pct[-1])
    fig.update_layout(**_base_layout(
        title=dict(
            text=(
                f"Performance Overview: Portfolio vs SPY | {t0} – {t1}  "
                f"<span style='color:{COLORS['muted']};font-size:12px'>"
                f"Final: {port_final:+.2f}% vs {spy_final:+.2f}%</span>"
            ),
            x=0.02,
        ),
        yaxis=dict(title="Cumulative Return (%)", ticksuffix="%"),
        xaxis=dict(title=""),
        height=460,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    ))
    return _write_chart(fig, output_dir, "desk-performance.html")


def generate_equity_curve(returns: pd.Series, output_dir: Path) -> Path:
    """Equity curve with high-water mark overlay -> equity-curve.html."""
    desk = _load_desk_timeline()
    if desk is not None:
        series = desk["series"]
        idx = pd.to_datetime(series["dates"])
        equity = pd.Series(series["portfolio_nav"], index=idx)
    else:
        equity = (1 + returns).cumprod() * 1_000_000
    hwm = equity.cummax()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=equity.index, y=equity.values,
        mode="lines", name="Portfolio NAV",
        line=dict(color=COLORS["positive"], width=2),
        fill="tozeroy", fillcolor="rgba(0,255,136,0.08)",
        hovertemplate="$%{y:,.0f}<extra>NAV</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=hwm.index, y=hwm.values,
        mode="lines", name="High-Water Mark",
        line=dict(color=COLORS["accent"], width=1, dash="dot"),
        hovertemplate="$%{y:,.0f}<extra>HWM</extra>",
    ))
    total_ret = (equity.iloc[-1] / equity.iloc[0] - 1) * 100
    fig.update_layout(**_base_layout(
        title=dict(text=f"Equity Curve  <span style='color:{COLORS['muted']};font-size:13px'>({total_ret:+.1f}% total)</span>", x=0.02),
        yaxis=dict(title="Portfolio Value ($)", tickformat="$,.0f"),
        xaxis=dict(title=""),
        height=420,
    ))
    return _write_chart(fig, output_dir, "equity-curve.html")


def generate_drawdown_profile(returns: pd.Series, output_dir: Path) -> Path:
    """Drawdown time series -> drawdown.html."""
    desk = _load_desk_timeline()
    if desk is not None:
        nav = pd.Series(
            desk["series"]["portfolio_nav"],
            index=pd.to_datetime(desk["series"]["dates"]),
        )
        peak = nav.cummax()
        dd = ((peak - nav) / peak).rename("drawdown")
    else:
        dd = _compute_drawdown(returns)
    max_dd = dd.max() * 100

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dd.index, y=-dd.values * 100,
        mode="lines", name="Drawdown",
        line=dict(color=COLORS["negative"], width=1.5),
        fill="tozeroy", fillcolor="rgba(255,51,102,0.15)",
        hovertemplate="%{y:.2f}%<extra>Drawdown</extra>",
    ))
    fig.update_layout(**_base_layout(
        title=dict(text=f"Drawdown Profile  <span style='color:{COLORS['muted']};font-size:13px'>(max {max_dd:.1f}%)</span>", x=0.02),
        yaxis=dict(title="Drawdown (%)", ticksuffix="%"),
        xaxis=dict(title=""),
        height=360,
    ))
    return _write_chart(fig, output_dir, "drawdown.html")


def generate_monthly_heatmap(returns: pd.Series, output_dir: Path) -> Path:
    """Monthly returns heatmap -> heatmap.html."""
    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1) * 100
    df = monthly.to_frame("ret")
    df["Year"] = df.index.year
    df["Month"] = df.index.strftime("%b")
    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    pivot = df.pivot(index="Year", columns="Month", values="ret")
    pivot = pivot.reindex(columns=[m for m in months_order if m in pivot.columns])

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, COLORS["negative"]],
            [0.5, COLORS["bg"]],
            [1.0, COLORS["positive"]],
        ],
        zmid=0,
        text=np.where(np.isnan(pivot.values), "", np.vectorize(lambda v: f"{v:.1f}%")(pivot.values)),
        texttemplate="%{text}",
        textfont=dict(size=11, color=COLORS["text"]),
        hovertemplate="Year %{y} %{x}: %{z:.2f}%<extra></extra>",
        colorbar=dict(title="Return %", ticksuffix="%"),
    ))
    fig.update_layout(**_base_layout(
        title=dict(text="Monthly Returns Heatmap", x=0.02),
        yaxis=dict(title="", autorange="reversed"),
        xaxis=dict(title="", side="top"),
        height=max(280, 80 + len(pivot) * 50),
    ))
    return _write_chart(fig, output_dir, "heatmap.html")


def generate_return_distribution(returns: pd.Series, output_dir: Path) -> Path:
    """Return distribution histogram with VaR -> return-dist.html."""
    pct = returns.values * 100
    var5 = float(np.percentile(pct, 5))
    cf_var = _cornish_fisher_var(returns.values) * 100

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=pct, nbinsx=70,
        name="Daily Returns",
        marker_color=COLORS["blue"], opacity=0.75,
        hovertemplate="%{x:.2f}%<br>Count: %{y}<extra></extra>",
    ))
    fig.add_vline(x=var5, line_dash="dash", line_color=COLORS["accent"], line_width=2,
                  annotation=dict(text=f"Hist VaR 5%: {var5:.2f}%", font=dict(color=COLORS["accent"], size=11)))
    fig.add_vline(x=cf_var, line_dash="dot", line_color=COLORS["purple"], line_width=2,
                  annotation=dict(text=f"CF VaR 5%: {cf_var:.2f}%", font=dict(color=COLORS["purple"], size=11), y=0.85))
    fig.update_layout(**_base_layout(
        title=dict(text="Daily Return Distribution", x=0.02),
        xaxis=dict(title="Return (%)", ticksuffix="%"),
        yaxis=dict(title="Frequency"),
        height=380,
        bargap=0.02,
    ))
    return _write_chart(fig, output_dir, "return-dist.html")


def generate_backtest_comparison(output_dir: Path) -> Path:
    """Grouped bar chart comparing backtest models -> backtest-compare.html."""
    bt_path = Path("docs/backtest-results.json")
    models: dict = {}
    if bt_path.exists():
        try:
            raw = json.loads(bt_path.read_text(encoding="utf-8"))
            models = {k: v for k, v in raw.items() if isinstance(v, dict) and "total_return" in v}
        except (json.JSONDecodeError, OSError):
            pass

    if not models:
        models = {
            "BWC Strategy": dict(total_return=0.053, annualized_sharpe=1.34, annualized_sortino=2.75, max_drawdown=-0.094),
            "Equal Weight": dict(total_return=0.041, annualized_sharpe=1.10, annualized_sortino=2.10, max_drawdown=-0.120),
        }

    display_labels = {
        "total_return": "Total Return",
        "annualized_sharpe": "Sharpe",
        "annualized_sortino": "Sortino",
        "max_drawdown": "Max Drawdown",
    }
    metric_keys = list(display_labels.keys())
    bar_colors = [COLORS["positive"], COLORS["blue"], COLORS["purple"], COLORS["accent"]]

    fig = go.Figure()
    for i, (name, vals) in enumerate(models.items()):
        fig.add_trace(go.Bar(
            x=[display_labels.get(k, k) for k in metric_keys],
            y=[float(vals.get(k, 0)) for k in metric_keys],
            name=name.replace("_", " ").title(),
            marker_color=bar_colors[i % len(bar_colors)],
            opacity=0.85,
            hovertemplate="%{x}: %{y:.4f}<extra>%{fullData.name}</extra>",
        ))
    fig.update_layout(**_base_layout(
        title=dict(text="Backtest Model Comparison", x=0.02),
        barmode="group",
        yaxis=dict(title="Value"),
        xaxis=dict(title=""),
        height=400,
    ))
    return _write_chart(fig, output_dir, "backtest-compare.html")


def generate_monte_carlo_fan(output_dir: Path) -> Path:
    """Monte Carlo simulation fan chart -> monte-carlo.html."""
    cum_paths = None
    terminal = None

    try:
        engine = _get_engine()
        if engine is None:
            raise RuntimeError("engine unavailable")
        paths, term = engine.run_monte_carlo(
            days_forward=_MC_DAYS, num_simulations=5000
        )
        if paths is not None and len(paths) > 0:
            cum_paths = np.cumprod(1 + paths, axis=1)
            terminal = term
            logger.info("Monte Carlo fan using REAL simulation (%d paths)", len(paths))
        else:
            raise ValueError("empty MC paths")
    except Exception as exc:
        logger.warning("Real Monte Carlo failed: %s — trying simulation module", exc)

    if cum_paths is None:
        try:
            from quant_monitor.backtest.simulation import run_monte_carlo_simulation
            rng = np.random.default_rng(42)
            hist = pd.DataFrame(rng.normal(0.0004, 0.012, (252, 3)), columns=["A", "B", "C"])
            _, terminal = run_monte_carlo_simulation(
                hist, days_forward=_MC_DAYS, num_simulations=5000
            )
            hist_series = pd.DataFrame(
                rng.normal(0.0004, 0.012, (252, 3)), columns=["A", "B", "C"]
            )
            paths, _ = run_monte_carlo_simulation(
                hist_series, days_forward=_MC_DAYS, num_simulations=5000
            )
            cum_paths = np.cumprod(1 + paths, axis=1)
        except Exception:
            rng = np.random.default_rng(42)
            n_sims, n_days = 5000, _MC_DAYS
            daily = rng.normal(0.0004, 0.012, (n_sims, n_days))
            cum_paths = np.cumprod(1 + daily, axis=1)
            terminal = cum_paths[:, -1] - 1

    days = np.arange(1, cum_paths.shape[1] + 1)
    percentiles = [5, 25, 50, 75, 95]
    pct_values = {p: np.percentile(cum_paths, p, axis=0) for p in percentiles}

    hurdle_pct = float(np.mean(terminal >= 0.03) * 100)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days, y=pct_values[95], mode="lines", name="95th pctl",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=days, y=pct_values[5], mode="lines", name="5th-95th",
        line=dict(width=0), fill="tonexty",
        fillcolor="rgba(59,130,246,0.12)",
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=days, y=pct_values[75], mode="lines", name="75th pctl",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=days, y=pct_values[25], mode="lines", name="25th-75th",
        line=dict(width=0), fill="tonexty",
        fillcolor="rgba(59,130,246,0.25)",
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=days, y=pct_values[50], mode="lines", name="Median Path",
        line=dict(color=COLORS["blue"], width=2.5),
        hovertemplate="Day %{x}: %{y:.4f}x<extra>Median</extra>",
    ))
    fig.add_hline(y=1.03, line_dash="dash", line_color=COLORS["accent"], line_width=1.5,
                  annotation=dict(text=f"+3% hurdle ({hurdle_pct:.1f}% prob)",
                                  font=dict(color=COLORS["accent"], size=11)))
    fig.add_hline(y=1.0, line_dash="dot", line_color=COLORS["muted"], line_width=1)

    fig.update_layout(**_base_layout(
        title=dict(
            text=f"Monte Carlo Forward Simulation ({_MC_DAYS}-day, valuation → sunset)",
            x=0.02,
        ),
        yaxis=dict(title="Wealth Multiplier", tickformat=".2f"),
        xaxis=dict(title="Trading Days Forward"),
        height=420,
    ))
    return _write_chart(fig, output_dir, "monte-carlo.html")


def _synthetic_correlation_data():
    """Generate synthetic correlation data as fallback."""
    rng = np.random.default_rng(42)
    assets = ["SPY", "TLT", "GLD", "VIX", "DXY", "BTC", "AAPL", "MSFT"]
    n = len(assets)
    raw = rng.normal(0, 0.01, (252, n))
    raw[:, 1] = -0.3 * raw[:, 0] + rng.normal(0, 0.008, 252)
    raw[:, 3] = -0.5 * raw[:, 0] + rng.normal(0, 0.015, 252)
    raw[:, 5] = 0.4 * raw[:, 0] + rng.normal(0, 0.02, 252)
    raw[:, 6] = 0.7 * raw[:, 0] + rng.normal(0, 0.008, 252)
    raw[:, 7] = 0.65 * raw[:, 0] + rng.normal(0, 0.008, 252)
    corr = np.corrcoef(raw.T)
    return assets, corr


def _real_correlation_data():
    """Fetch real correlation matrix from portfolio tickers via yfinance."""
    import yfinance as yf

    from quant_monitor.config import cfg

    tickers = cfg.tickers
    if not tickers:
        raise ValueError("No tickers in config")
    data = yf.download(tickers, period="1y", auto_adjust=True, progress=False)
    closes = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data
    closes = closes.dropna(axis=1, how="all").dropna()
    if closes.shape[1] < 2 or len(closes) < 20:
        raise ValueError("Insufficient price data for correlation")
    assets = list(closes.columns)
    corr = closes.pct_change().dropna().corr().values
    return assets, corr


def generate_correlation_network(output_dir: Path) -> Path:
    """3D correlation network graph -> correlation-graph.html."""
    try:
        assets, corr = _real_correlation_data()
        logger.info("Correlation network using REAL data (%d assets)", len(assets))
    except Exception as exc:
        logger.warning("Real correlation data failed: %s — using synthetic", exc)
        assets, corr = _synthetic_correlation_data()

    rng = np.random.default_rng(42)
    n = len(assets)

    theta = np.linspace(0, 2 * np.pi, n, endpoint=False)
    radius = 2.0
    x_pos = radius * np.cos(theta)
    y_pos = radius * np.sin(theta)
    z_pos = rng.uniform(-0.5, 0.5, n)

    edge_x, edge_y, edge_z = [], [], []
    threshold = 0.25
    for i in range(n):
        for j in range(i + 1, n):
            if abs(corr[i, j]) > threshold:
                edge_x += [x_pos[i], x_pos[j], None]
                edge_y += [y_pos[i], y_pos[j], None]
                edge_z += [z_pos[i], z_pos[j], None]

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode="lines",
        line=dict(color=COLORS["muted"], width=2),
        hoverinfo="skip", showlegend=False,
    ))

    node_colors = [corr[i].mean() for i in range(n)]
    fig.add_trace(go.Scatter3d(
        x=x_pos, y=y_pos, z=z_pos,
        mode="markers+text",
        marker=dict(
            size=12, color=node_colors,
            colorscale=[[0, COLORS["negative"]], [0.5, COLORS["muted"]], [1, COLORS["positive"]]],
            colorbar=dict(title="Avg rho", len=0.6),
            line=dict(width=1, color=COLORS["text"]),
        ),
        text=assets,
        textposition="top center",
        textfont=dict(size=11, color=COLORS["text"]),
        hovertemplate="%{text}<br>Avg rho: %{marker.color:.2f}<extra></extra>",
        showlegend=False,
    ))

    fig.update_layout(**_base_layout(
        title=dict(text="3D Asset Correlation Network", x=0.02),
        height=520,
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor=COLORS["bg"],
            camera=dict(eye=dict(x=1.6, y=1.6, z=1.0)),
        ),
    ))
    return _write_chart(fig, output_dir, "correlation-graph.html")


def generate_factor_loadings(output_dir: Path) -> Path:
    """Factor beta bar chart -> factor-loadings.html."""
    rng = np.random.default_rng(42)

    try:
        engine = _get_engine()
        if engine is None:
            raise RuntimeError("engine unavailable")
        reg = engine.run_factor_regression()
        if "error" in reg:
            raise ValueError(reg["error"])
        factors = ["Market (β)", "Size (SMB)", "Value (HML)", "Momentum"]
        betas = [
            reg["ff3_beta_mkt"],
            reg["ff3_beta_smb"],
            reg["ff3_beta_hml"],
            reg["c4_beta_mom"],
        ]
        errors = [0.0] * len(factors)
        logger.info("Factor loadings using REAL regression data")
    except Exception as exc:
        logger.warning("Real factor loadings failed: %s — using synthetic", exc)
        factors = ["Market (β)", "Size (SMB)", "Value (HML)", "Momentum", "Quality", "Low Vol"]
        betas = [0.82, -0.15, 0.23, 0.41, 0.35, 0.18]
        errors = rng.uniform(0.04, 0.12, len(factors))

    colors = [COLORS["positive"] if b >= 0 else COLORS["negative"] for b in betas]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=factors, y=betas,
        marker_color=colors, opacity=0.85,
        error_y=dict(type="data", array=errors, color=COLORS["muted"], thickness=1.5),
        hovertemplate="%{x}: β = %{y:.2f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=COLORS["muted"], line_width=1)
    fig.update_layout(**_base_layout(
        title=dict(text="Factor Loadings (Betas)", x=0.02),
        yaxis=dict(title="Beta Coefficient"),
        xaxis=dict(title=""),
        height=380,
    ))
    return _write_chart(fig, output_dir, "factor-loadings.html")


def _synthetic_brinson_data():
    """Generate synthetic Brinson attribution data as fallback."""
    rng = np.random.default_rng(42)
    periods = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025", "Q1 2026"]
    allocation = rng.normal(0.005, 0.003, len(periods))
    selection = rng.normal(0.008, 0.004, len(periods))
    interaction = rng.normal(0.001, 0.002, len(periods))
    return periods, allocation, selection, interaction


def generate_brinson_attribution(output_dir: Path) -> Path:
    """Brinson attribution stacked bar -> attribution.html."""
    try:
        engine = _get_engine()
        if engine is None:
            raise RuntimeError("engine unavailable")
        attr_df = engine.run_brinson_attribution()
        if attr_df.empty:
            raise ValueError("empty attribution result")
        periods = list(attr_df.index)
        allocation = attr_df["Allocation"].values
        selection = attr_df["Selection"].values
        interaction = attr_df["Interaction"].values
        logger.info("Brinson attribution using REAL data (%d sectors)", len(periods))
    except Exception as exc:
        logger.warning("Real Brinson attribution failed: %s — using synthetic", exc)
        periods, allocation, selection, interaction = _synthetic_brinson_data()

    fig = go.Figure()
    for vals, name, color in [
        (allocation, "Allocation", COLORS["blue"]),
        (selection, "Selection", COLORS["positive"]),
        (interaction, "Interaction", COLORS["purple"]),
    ]:
        fig.add_trace(go.Bar(
            x=periods, y=vals * 100,
            name=name, marker_color=color, opacity=0.85,
            hovertemplate="%{x}: %{y:.2f}%<extra>" + name + "</extra>",
        ))
    fig.add_hline(y=0, line_color=COLORS["muted"], line_width=1)
    fig.update_layout(**_base_layout(
        title=dict(text="Brinson Performance Attribution", x=0.02),
        barmode="relative",
        yaxis=dict(title="Contribution (%)", ticksuffix="%"),
        xaxis=dict(title=""),
        height=400,
    ))
    return _write_chart(fig, output_dir, "attribution.html")


# ---------------------------------------------------------------------------
# Aggregate generators
# ---------------------------------------------------------------------------

def generate_results_json(returns: pd.Series, output_dir: Path) -> Path:
    """Compute KPIs and write results.json."""
    results: dict | None = None

    try:
        engine = _get_engine()
        if engine is None:
            raise RuntimeError("engine unavailable")
        metrics = engine.compute_all_metrics()
        if not metrics:
            raise ValueError("empty metrics")

        # Monte Carlo hurdle via engine
        try:
            _, terminal = engine.run_monte_carlo(
                days_forward=_MC_DAYS, num_simulations=10_000
            )
            if terminal is not None and len(terminal) > 0:
                hurdle_pct = float(np.mean(terminal >= 0.03) * 100)
            else:
                raise ValueError("empty MC result")
        except Exception:
            rng = np.random.default_rng(42)
            terminal = np.cumprod(
                1 + rng.normal(0.0004, 0.012, (10000, _MC_DAYS)), axis=1
            )[:, -1] - 1
            hurdle_pct = float(np.mean(terminal >= 0.03) * 100)

        results = {
            "total_return": metrics.get("total_return", 0),
            "annualized_return": metrics.get("annualized_return", 0),
            "sharpe": metrics.get("sharpe_ratio", 0),
            "sortino": metrics.get("sortino_ratio", 0),
            "max_drawdown": metrics.get("max_drawdown", 0),
            "calmar": metrics.get("calmar_ratio", 0),
            "monte_carlo_hurdle_pct": round(hurdle_pct, 2),
            "cornish_fisher_var_5pct": metrics.get("cornish_fisher_var", 0),
            "portfolio_beta": metrics.get("beta", 0.82),
        }
        logger.info("Results JSON using REAL metrics")
    except Exception as exc:
        logger.warning("Real metrics failed: %s — computing from returns", exc)

    if results is None:
        equity = (1 + returns).cumprod()
        total_return = float(equity.iloc[-1] / equity.iloc[0] - 1)
        ann_return = float((1 + returns.mean()) ** 252 - 1)
        sharpe = float(returns.mean() / returns.std() * np.sqrt(252))

        downside = returns[returns < 0]
        sortino = float(returns.mean() / downside.std() * np.sqrt(252)) if len(downside) > 0 else 0.0

        dd = _compute_drawdown(returns)
        max_dd = float(dd.max())
        calmar = float(ann_return / max_dd) if max_dd > 0 else 0.0

        cf_var = float(_cornish_fisher_var(returns.values))
        portfolio_beta = 0.82

        try:
            from quant_monitor.backtest.simulation import run_monte_carlo_simulation
            rng = np.random.default_rng(42)
            hist = pd.DataFrame(rng.normal(0.0004, 0.012, (252, 3)), columns=["A", "B", "C"])
            _, terminal = run_monte_carlo_simulation(
                hist, days_forward=_MC_DAYS, num_simulations=10000
            )
        except Exception:
            rng = np.random.default_rng(42)
            terminal = np.cumprod(
                1 + rng.normal(0.0004, 0.012, (10000, _MC_DAYS)), axis=1
            )[:, -1] - 1

        hurdle_pct = float(np.mean(terminal >= 0.03) * 100)

        results = {
            "total_return": round(total_return, 6),
            "annualized_return": round(ann_return, 6),
            "sharpe": round(sharpe, 4),
            "sortino": round(sortino, 4),
            "max_drawdown": round(max_dd, 6),
            "calmar": round(calmar, 4),
            "monte_carlo_hurdle_pct": round(hurdle_pct, 2),
            "cornish_fisher_var_5pct": round(cf_var, 6),
            "portfolio_beta": portfolio_beta,
        }

    # Compute win_rate and profit_factor from the trade log
    win_rate_val = 0.0
    profit_factor_val = 0.0
    try:
        engine = _get_engine()
        if engine is not None:
            log = engine.get_trade_log()
            sells = log[log["action"] == "SELL"]
            if not sells.empty:
                wins = sells[sells["amount"] > 0]["amount"].sum()
                losses = abs(sells[sells["amount"] <= 0]["amount"].sum())
                total_sells = len(sells)
                winning_sells = len(sells[sells["amount"] > 0])
                win_rate_val = (winning_sells / total_sells * 100) if total_sells > 0 else 0.0
                profit_factor_val = (wins / losses) if losses > 0 else wins if wins > 0 else 0.0
    except Exception:
        pass

    results["win_rate_raw"] = round(win_rate_val, 2)
    results["profit_factor_raw"] = round(profit_factor_val, 2)

    # Add frontend-friendly aliases (main.js expects these display-ready keys)
    mc = results.get("monte_carlo_hurdle_pct", 0)
    cfv = results.get("cornish_fisher_var_5pct", 0)
    beta = results.get("portfolio_beta", 0)
    mdd = results.get("max_drawdown", 0)
    ann = results.get("annualized_return", 0)
    sr = results.get("sharpe", 0)
    so = results.get("sortino", 0)
    cal = results.get("calmar", 0)

    results["mc_hurdle"] = f"{mc:.1f}%"
    results["cf_var"] = f"{cfv * 100:+.2f}%" if abs(cfv) < 1 else f"{cfv:+.2f}%"
    results["beta"] = f"{beta:.2f}"
    results["max_dd"] = f"{mdd * 100:+.1f}%" if abs(mdd) < 1 else f"{mdd:+.1f}%"
    results["ann_return"] = f"{ann * 100:+.1f}%" if abs(ann) < 1 else f"{ann:+.1f}%"
    results["sharpe"] = f"{sr:.2f}"
    results["sortino"] = f"{so:.2f}"
    results["calmar"] = f"{cal:.2f}"
    results["win_rate"] = f"{win_rate_val:.1f}%"
    results["profit_factor"] = f"{profit_factor_val:.2f}"

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "results.json"
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    logger.info("Results JSON written → %s", path)
    return path


def generate_all_charts(output_dir: str | Path = "frontend/charts") -> list[Path]:
    """Generate every chart and the results JSON. Returns list of output paths."""
    out = Path(output_dir)
    returns = _get_real_returns()

    paths: list[Path] = []
    desk_perf = generate_desk_performance(out)
    if desk_perf is not None:
        paths.append(desk_perf)

    paths.extend([
        generate_equity_curve(returns, out),
        generate_drawdown_profile(returns, out),
        generate_monthly_heatmap(returns, out),
        generate_return_distribution(returns, out),
        generate_backtest_comparison(out),
        generate_monte_carlo_fan(out),
        generate_correlation_network(out),
        generate_factor_loadings(out),
        generate_brinson_attribution(out),
        generate_results_json(returns, out),
    ])

    print(f"✅ Generated {len(paths)} artifacts → {out.resolve()}")
    return paths


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Generate embeddable Plotly chart files for BWC frontend")
    parser.add_argument("--output-dir", type=str, default="frontend/charts",
                        help="Directory for generated chart HTML files (default: frontend/charts)")
    args = parser.parse_args()
    generate_all_charts(output_dir=args.output_dir)
