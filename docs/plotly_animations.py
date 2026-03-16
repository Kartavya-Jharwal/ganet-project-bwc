"""
Project BWC — Plotly + Matplotlib Animated Visualizations
Dark theme throughout. Interactive HTML outputs. Advanced statistical viz.
Run: python docs/plotly_animations.py
Outputs to: docs/viz_output/
"""

import numpy as np
from pathlib import Path
from scipy import stats
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

OUT = Path(__file__).parent / "viz_output"
OUT.mkdir(exist_ok=True)

# ── Dark Theme ───────────────────────────────────────────────────────────────

DARK_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#0a0a0a",
        font=dict(color="#e4e4e7", family="Inter, system-ui, sans-serif", size=13),
        title_font=dict(size=20, color="#f4f4f5"),
        xaxis=dict(gridcolor="#1e1e2e", zerolinecolor="#27272a", linecolor="#27272a"),
        yaxis=dict(gridcolor="#1e1e2e", zerolinecolor="#27272a", linecolor="#27272a"),
        colorway=[
            "#3b82f6", "#00ff88", "#eb5e28", "#8b5cf6",
            "#ff3366", "#14b8a6", "#f59e0b", "#f4f4f5",
        ],
        margin=dict(l=60, r=40, t=80, b=60),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#27272a"),
    )
)

BLU = "#3b82f6"
POS = "#00ff88"
ACCENT = "#eb5e28"
PUR = "#8b5cf6"
NEG = "#ff3366"
TEAL = "#14b8a6"
GOLD = "#f59e0b"
WHT = "#f4f4f5"
MUTED = "#52525b"


def dark_layout(**overrides):
    base = {
        "paper_bgcolor": "#0a0a0a",
        "plot_bgcolor": "#0a0a0a",
        "font": dict(color="#e4e4e7", family="Inter, system-ui, sans-serif", size=13),
        "xaxis": dict(gridcolor="#1e1e2e", zerolinecolor="#27272a"),
        "yaxis": dict(gridcolor="#1e1e2e", zerolinecolor="#27272a"),
        "margin": dict(l=60, r=40, t=80, b=60),
        "legend": dict(bgcolor="rgba(0,0,0,0)", bordercolor="#27272a"),
    }
    base.update(overrides)
    return base


# ═════════════════════════════════════════════════════════════════════════════
#  1. MONTE CARLO SDE — Animated Path Explosion
# ═════════════════════════════════════════════════════════════════════════════

def viz_monte_carlo_sde():
    import plotly.graph_objects as go

    np.random.seed(42)
    n_paths, n_steps = 80, 200
    dt = 0.01
    mu, sigma = 0.08, 0.20
    t = np.linspace(0, n_steps * dt, n_steps + 1)

    paths = np.zeros((n_paths, n_steps + 1))
    paths[:, 0] = 100
    for i in range(n_steps):
        z = np.random.normal(size=n_paths)
        paths[:, i + 1] = paths[:, i] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)

    frames = []
    steps_per_frame = 5
    for k in range(1, n_steps + 1, steps_per_frame):
        traces = []
        for j in range(n_paths):
            traces.append(go.Scatter(
                x=t[:k + 1], y=paths[j, :k + 1],
                mode="lines", line=dict(width=0.8, color=BLU),
                opacity=0.15, showlegend=False,
            ))
        frames.append(go.Frame(data=traces, name=str(k)))

    init_traces = [go.Scatter(
        x=[0], y=[100], mode="lines",
        line=dict(width=0.8, color=BLU), opacity=0.15, showlegend=False,
    ) for _ in range(n_paths)]

    fig = go.Figure(data=init_traces, frames=frames)

    # Terminal distribution
    terminal = paths[:, -1]
    fig.add_trace(go.Histogram(
        y=terminal, nbinsy=30, marker_color=ACCENT, opacity=0.6,
        xaxis="x2", showlegend=False, name="Terminal Dist",
    ))

    var_5 = np.percentile(terminal, 5)
    fig.add_hline(y=var_5, line_dash="dash", line_color=NEG, annotation_text=f"VaR 5% = {var_5:.1f}")

    fig.update_layout(
        **dark_layout(
            title="Geometric Brownian Motion — Monte Carlo SDE Paths",
            xaxis_title="Time (years)", yaxis_title="S(t)",
            xaxis2=dict(overlaying="x", side="top", showgrid=False, showticklabels=False, range=[0, 12]),
        ),
        updatemenus=[dict(
            type="buttons", showactive=False, x=0.05, y=1.12,
            buttons=[
                dict(label="▶ Play", method="animate",
                     args=[None, dict(frame=dict(duration=40, redraw=True), fromcurrent=True)]),
                dict(label="⏸", method="animate",
                     args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
            ],
        )],
    )
    fig.write_html(str(OUT / "01_monte_carlo_sde.html"), include_plotlyjs="cdn")
    print("  ✓ 01_monte_carlo_sde.html")


# ═════════════════════════════════════════════════════════════════════════════
#  2. EFFICIENT FRONTIER — Interactive Portfolio Cloud
# ═════════════════════════════════════════════════════════════════════════════

def viz_efficient_frontier():
    import plotly.graph_objects as go

    np.random.seed(99)
    n = 5000
    vols = np.random.uniform(0.04, 0.35, n)
    caps = 0.18 * np.sqrt(np.maximum(vols - 0.04, 0) / 0.28)
    rets = np.array([np.random.uniform(0.005, max(c, 0.006)) for c in caps])
    sharpes = (rets - 0.02) / vols

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=vols, y=rets, mode="markers",
        marker=dict(size=3, color=sharpes, colorscale="Viridis", colorbar=dict(title="Sharpe"), opacity=0.5),
        name="Portfolios", text=[f"σ={v:.2%} μ={r:.2%} SR={s:.2f}" for v, r, s in zip(vols, rets, sharpes)],
    ))

    # Frontier curve
    frontier_x = np.linspace(0.04, 0.33, 200)
    frontier_y = 0.18 * np.sqrt(np.maximum(frontier_x - 0.04, 0) / 0.28)
    fig.add_trace(go.Scatter(
        x=frontier_x, y=frontier_y, mode="lines",
        line=dict(color=POS, width=3), name="Efficient Frontier",
    ))

    # CML
    tang_x = 0.12
    tang_y = 0.18 * np.sqrt((tang_x - 0.04) / 0.28)
    slope = (tang_y - 0.02) / tang_x
    cml_x = np.linspace(0, 0.33, 100)
    fig.add_trace(go.Scatter(
        x=cml_x, y=0.02 + slope * cml_x, mode="lines",
        line=dict(color=ACCENT, width=2, dash="dash"), name="Capital Market Line",
    ))

    fig.add_trace(go.Scatter(
        x=[tang_x], y=[tang_y], mode="markers",
        marker=dict(size=14, color=ACCENT, symbol="star"),
        name="Tangency Portfolio (w*)",
    ))

    fig.update_layout(**dark_layout(
        title="Markowitz Efficient Frontier — 5,000 Random Portfolios",
        xaxis_title="Volatility (σ)", yaxis_title="Expected Return E[R]",
    ))
    fig.write_html(str(OUT / "02_efficient_frontier.html"), include_plotlyjs="cdn")
    print("  ✓ 02_efficient_frontier.html")


# ═════════════════════════════════════════════════════════════════════════════
#  3. VaR / CVaR — Animated Confidence Sweep
# ═════════════════════════════════════════════════════════════════════════════

def viz_var_cvar_sweep():
    import plotly.graph_objects as go

    x = np.linspace(-4.5, 4.5, 500)
    pdf = stats.norm.pdf(x)

    frames = []
    for alpha in np.linspace(0.01, 0.15, 50):
        z_alpha = stats.norm.ppf(alpha)
        cvar = -stats.norm.pdf(z_alpha) / alpha

        fill_x = x[x <= z_alpha]
        fill_y = stats.norm.pdf(fill_x)

        frame_data = [
            go.Scatter(x=x, y=pdf, mode="lines", line=dict(color=WHT, width=2), name="N(0,1)"),
            go.Scatter(
                x=np.concatenate([fill_x, fill_x[::-1]]),
                y=np.concatenate([fill_y, np.zeros_like(fill_y)]),
                fill="toself", fillcolor=f"rgba(255,51,102,{min(alpha * 5, 0.6):.2f})",
                line=dict(width=0), name=f"Tail α={alpha:.1%}",
            ),
            go.Scatter(
                x=[z_alpha, z_alpha], y=[0, stats.norm.pdf(z_alpha)],
                mode="lines", line=dict(color=NEG, width=2, dash="dash"),
                name=f"VaR = {z_alpha:.3f}",
            ),
            go.Scatter(
                x=[cvar], y=[0], mode="markers",
                marker=dict(size=12, color=ACCENT, symbol="diamond"),
                name=f"CVaR = {cvar:.3f}",
            ),
        ]
        frames.append(go.Frame(data=frame_data, name=f"{alpha:.3f}"))

    fig = go.Figure(data=frames[0].data, frames=frames)

    fig.update_layout(
        **dark_layout(
            title="VaR & CVaR — Animated Confidence Level Sweep",
            xaxis_title="Return (σ units)", yaxis_title="Density",
        ),
        updatemenus=[dict(
            type="buttons", showactive=False, x=0.05, y=1.12,
            buttons=[
                dict(label="▶ Sweep α", method="animate",
                     args=[None, dict(frame=dict(duration=80, redraw=True), fromcurrent=True)]),
            ],
        )],
        sliders=[dict(
            active=0, steps=[
                dict(args=[[f.name], dict(frame=dict(duration=0, redraw=True), mode="immediate")],
                     label=f"{float(f.name):.1%}", method="animate")
                for f in frames[::5]
            ],
            x=0.05, len=0.9, xanchor="left", y=-0.05,
            currentvalue=dict(prefix="α = ", visible=True, font=dict(color=WHT)),
            font=dict(color=MUTED),
        )],
    )
    fig.write_html(str(OUT / "03_var_cvar_sweep.html"), include_plotlyjs="cdn")
    print("  ✓ 03_var_cvar_sweep.html")


# ═════════════════════════════════════════════════════════════════════════════
#  4. STOCHASTIC VOL SURFACE — 3D Interactive
# ═════════════════════════════════════════════════════════════════════════════

def viz_vol_surface_3d():
    import plotly.graph_objects as go

    moneyness = np.linspace(0.7, 1.3, 80)
    maturity = np.linspace(0.05, 2.0, 80)
    M, T = np.meshgrid(moneyness, maturity)

    base = 0.20 + 0.05 * np.exp(-T)
    smile = 0.15 * (M - 1.0) ** 2
    skew = -0.08 * (M - 1.0) * np.exp(-0.5 * T)
    wings = 0.02 * np.exp(-2.0 * T) * (M - 1.0) ** 4
    vol = np.clip(base + smile + skew + wings, 0.05, 0.60)

    fig = go.Figure(data=[go.Surface(
        x=moneyness, y=maturity, z=vol,
        colorscale=[
            [0.0, POS], [0.25, BLU], [0.5, PUR], [0.75, ACCENT], [1.0, NEG],
        ],
        contours_z=dict(show=True, usecolormap=True, highlightcolor=WHT, project_z=True),
        opacity=0.9,
    )])

    fig.update_layout(
        title="Implied Volatility Surface σ(K/S, T)",
        scene=dict(
            xaxis=dict(title="Moneyness K/S", backgroundcolor="#0a0a0a", gridcolor="#1e1e2e", color=WHT),
            yaxis=dict(title="Maturity T (yr)", backgroundcolor="#0a0a0a", gridcolor="#1e1e2e", color=WHT),
            zaxis=dict(title="Implied Vol σ", backgroundcolor="#0a0a0a", gridcolor="#1e1e2e", color=WHT),
            bgcolor="#0a0a0a",
            camera=dict(eye=dict(x=1.8, y=-1.5, z=1.2)),
        ),
        paper_bgcolor="#0a0a0a", font=dict(color=WHT),
        margin=dict(l=0, r=0, t=60, b=0),
    )
    fig.write_html(str(OUT / "04_vol_surface_3d.html"), include_plotlyjs="cdn")
    print("  ✓ 04_vol_surface_3d.html")


# ═════════════════════════════════════════════════════════════════════════════
#  5. REGIME DETECTION — Animated State Machine
# ═════════════════════════════════════════════════════════════════════════════

def viz_regime_detection():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    np.random.seed(42)
    n_days = 500
    t = np.arange(n_days)

    # Simulated macro signals
    vix = 15 + 5 * np.sin(t / 80) + np.random.normal(0, 2, n_days)
    vix[200:260] += 18  # crisis spike
    vix[350:380] += 12  # transition

    spread = 1.5 - 0.003 * t + np.random.normal(0, 0.15, n_days)
    spread[200:260] -= 1.5
    spread[350:380] -= 0.8

    regime = []
    for v, s in zip(vix, spread):
        crisis_count = int(v > 25) + int(s < 0) + int(v > 35)
        if crisis_count >= 3:
            regime.append("CRISIS")
        elif crisis_count >= 1:
            regime.append("TRANSITION")
        else:
            regime.append("RISK_ON")

    regime_colors = {"RISK_ON": POS, "TRANSITION": GOLD, "CRISIS": NEG}
    bg_colors = [regime_colors[r] for r in regime]

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        subplot_titles=["VIX Index", "Yield Curve Spread (10Y-2Y)", "Detected Regime"])

    fig.add_trace(go.Scatter(
        x=t, y=vix, mode="lines", line=dict(color=BLU, width=1.5), name="VIX",
    ), row=1, col=1)
    fig.add_hline(y=25, line_dash="dash", line_color=GOLD, row=1, col=1)
    fig.add_hline(y=35, line_dash="dash", line_color=NEG, row=1, col=1)

    fig.add_trace(go.Scatter(
        x=t, y=spread, mode="lines", line=dict(color=PUR, width=1.5), name="10Y-2Y Spread",
    ), row=2, col=1)
    fig.add_hline(y=0, line_dash="dash", line_color=NEG, row=2, col=1)

    fig.add_trace(go.Bar(
        x=t, y=[1] * n_days, marker_color=bg_colors, showlegend=False,
    ), row=3, col=1)

    for name, color in regime_colors.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color), name=name,
        ), row=3, col=1)

    fig.update_layout(**dark_layout(
        title="Macro Regime Detection — VIX + Yield Curve",
        height=700,
    ))
    for i in range(1, 4):
        fig.update_xaxes(gridcolor="#1e1e2e", row=i, col=1)
        fig.update_yaxes(gridcolor="#1e1e2e", row=i, col=1)
    fig.write_html(str(OUT / "05_regime_detection.html"), include_plotlyjs="cdn")
    print("  ✓ 05_regime_detection.html")


# ═════════════════════════════════════════════════════════════════════════════
#  6. BLACK-LITTERMAN — Prior/View/Posterior Distribution Morph
# ═════════════════════════════════════════════════════════════════════════════

def viz_black_litterman():
    import plotly.graph_objects as go

    x = np.linspace(-0.05, 0.30, 500)

    prior_mu, prior_sig = 0.08, 0.04
    view_mu, view_sig = 0.15, 0.03

    frames = []
    for blend in np.linspace(0, 1, 60):
        post_mu = (1 - blend) * prior_mu + blend * 0.11
        post_sig = (1 - blend) * prior_sig + blend * 0.025

        frame_data = [
            go.Scatter(x=x, y=stats.norm.pdf(x, prior_mu, prior_sig),
                       mode="lines", line=dict(color=BLU, width=2, dash="dot"),
                       name="Market Prior Π", opacity=0.5),
            go.Scatter(x=x, y=stats.norm.pdf(x, view_mu, view_sig),
                       mode="lines", line=dict(color=GOLD, width=2, dash="dot"),
                       name="Investor Views Q", opacity=0.5),
            go.Scatter(x=x, y=stats.norm.pdf(x, post_mu, post_sig),
                       mode="lines", line=dict(color=POS, width=3),
                       name=f"Posterior E[R] (μ={post_mu:.3f})"),
        ]
        frames.append(go.Frame(data=frame_data, name=f"{blend:.2f}"))

    fig = go.Figure(data=frames[0].data, frames=frames)
    fig.update_layout(
        **dark_layout(
            title="Black-Litterman: Prior → Posterior Convergence",
            xaxis_title="Expected Return", yaxis_title="Density",
        ),
        updatemenus=[dict(
            type="buttons", showactive=False, x=0.05, y=1.12,
            buttons=[dict(label="▶ Blend", method="animate",
                          args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True)])],
        )],
    )
    fig.write_html(str(OUT / "06_black_litterman.html"), include_plotlyjs="cdn")
    print("  ✓ 06_black_litterman.html")


# ═════════════════════════════════════════════════════════════════════════════
#  7. HRP DENDROGRAM + CORRELATION HEATMAP
# ═════════════════════════════════════════════════════════════════════════════

def viz_hrp_clustering():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.figure_factory as ff

    tickers = ["AAPL", "NVDA", "TSLA", "PLTR", "IONQ", "MSFT", "GOOG", "AMZN"]
    np.random.seed(42)
    n = 252
    base_corr = np.array([
        [1.0, 0.7, 0.4, 0.5, 0.3, 0.8, 0.75, 0.7],
        [0.7, 1.0, 0.5, 0.6, 0.4, 0.65, 0.6, 0.55],
        [0.4, 0.5, 1.0, 0.6, 0.5, 0.35, 0.3, 0.35],
        [0.5, 0.6, 0.6, 1.0, 0.55, 0.4, 0.35, 0.4],
        [0.3, 0.4, 0.5, 0.55, 1.0, 0.25, 0.2, 0.25],
        [0.8, 0.65, 0.35, 0.4, 0.25, 1.0, 0.85, 0.8],
        [0.75, 0.6, 0.3, 0.35, 0.2, 0.85, 1.0, 0.82],
        [0.7, 0.55, 0.35, 0.4, 0.25, 0.8, 0.82, 1.0],
    ])

    dist = np.sqrt(0.5 * (1 - base_corr))
    np.fill_diagonal(dist, 0)
    condensed = squareform(dist)
    Z = linkage(condensed, method="single")

    # Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=base_corr, x=tickers, y=tickers,
        colorscale=[[0, "#0a0a0a"], [0.5, PUR], [1.0, POS]],
        zmin=-0.2, zmax=1.0,
        text=np.round(base_corr, 2), texttemplate="%{text}",
        textfont=dict(size=11, color=WHT),
    ))
    fig.update_layout(**dark_layout(
        title="Correlation Matrix + HRP Distance D = √(½(1−ρ))",
        height=550, width=650,
    ))
    fig.write_html(str(OUT / "07_hrp_correlation.html"), include_plotlyjs="cdn")

    # Dendrogram via matplotlib (saved as image)
    import matplotlib.pyplot as plt
    plt.style.use("dark_background")
    fig_d, ax = plt.subplots(figsize=(10, 5))
    ax.set_facecolor("#0a0a0a")
    fig_d.patch.set_facecolor("#0a0a0a")
    dendrogram(Z, labels=tickers, ax=ax, color_threshold=0.4,
               above_threshold_color=MUTED, leaf_font_size=12)
    ax.set_title("HRP Dendrogram — Single-Linkage Clustering", color=WHT, fontsize=16)
    ax.tick_params(colors=WHT)
    ax.spines["bottom"].set_color("#27272a")
    ax.spines["left"].set_color("#27272a")
    fig_d.tight_layout()
    fig_d.savefig(str(OUT / "07_hrp_dendrogram.png"), dpi=200, facecolor="#0a0a0a")
    plt.close(fig_d)
    print("  ✓ 07_hrp_correlation.html + 07_hrp_dendrogram.png")


# ═════════════════════════════════════════════════════════════════════════════
#  8. BACKTEST ENGINE — Animated Equity Curve + Drawdown
# ═════════════════════════════════════════════════════════════════════════════

def viz_backtest_equity():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    np.random.seed(7)
    n_days = 1500
    t = np.arange(n_days)
    dates = np.array([f"2018-01-{(i % 28) + 1:02d}" for i in range(n_days)])

    bench_ret = np.random.normal(0.0003, 0.012, n_days)
    strat_ret = np.random.normal(0.0006, 0.009, n_days)

    bench_ret[400:450] -= 0.015  # COVID crash
    strat_ret[400:450] -= 0.005  # hedged

    bench_nav = 100 * np.exp(np.cumsum(bench_ret))
    strat_nav = 100 * np.exp(np.cumsum(strat_ret))

    bench_peak = np.maximum.accumulate(bench_nav)
    strat_peak = np.maximum.accumulate(strat_nav)
    bench_dd = (bench_nav - bench_peak) / bench_peak
    strat_dd = (strat_nav - strat_peak) / strat_peak

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08,
                        row_heights=[0.65, 0.35],
                        subplot_titles=["Equity Curve (NAV)", "Drawdown"])

    # Animated equity build
    frames = []
    step = 10
    for k in range(step, n_days + 1, step):
        frames.append(go.Frame(data=[
            go.Scatter(x=t[:k], y=bench_nav[:k], mode="lines", line=dict(color=MUTED, width=1.5), name="S&P 500"),
            go.Scatter(x=t[:k], y=strat_nav[:k], mode="lines", line=dict(color=POS, width=2.5), name="BWC Strategy"),
            go.Scatter(x=t[:k], y=bench_dd[:k], mode="lines", line=dict(color=MUTED, width=1), name="Bench DD"),
            go.Scatter(x=t[:k], y=strat_dd[:k], mode="lines", line=dict(color=POS, width=1.5), name="BWC DD"),
        ], name=str(k)))

    fig.add_trace(go.Scatter(x=t, y=bench_nav, mode="lines", line=dict(color=MUTED, width=1.5), name="S&P 500"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=strat_nav, mode="lines", line=dict(color=POS, width=2.5), name="BWC Strategy"), row=1, col=1)
    fig.add_trace(go.Scatter(x=t, y=bench_dd, mode="lines", line=dict(color=MUTED, width=1), name="Bench DD", showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=t, y=strat_dd, mode="lines", line=dict(color=POS, width=1.5), name="BWC DD", showlegend=False), row=2, col=1)

    sharpe = np.mean(strat_ret) / np.std(strat_ret) * np.sqrt(252)
    sortino_down = strat_ret[strat_ret < 0]
    sortino = np.mean(strat_ret) / np.std(sortino_down) * np.sqrt(252) if len(sortino_down) > 0 else 0
    max_dd = np.min(strat_dd)
    cagr = (strat_nav[-1] / 100) ** (252 / n_days) - 1

    fig.add_annotation(
        x=0.02, y=0.98, xref="paper", yref="paper", showarrow=False,
        text=f"Sharpe: {sharpe:.2f} | Sortino: {sortino:.2f} | CAGR: {cagr:.1%} | Max DD: {max_dd:.1%}",
        font=dict(color=POS, size=13), bgcolor="rgba(0,0,0,0.7)",
    )

    fig.update_layout(**dark_layout(title="Backtest Engine — Walk-Forward Simulation", height=650))
    for i in range(1, 3):
        fig.update_xaxes(gridcolor="#1e1e2e", row=i, col=1)
        fig.update_yaxes(gridcolor="#1e1e2e", row=i, col=1)
    fig.write_html(str(OUT / "08_backtest_equity.html"), include_plotlyjs="cdn")
    print("  ✓ 08_backtest_equity.html")


# ═════════════════════════════════════════════════════════════════════════════
#  9. FAMA-FRENCH ATTRIBUTION — Interactive Factor Decomposition
# ═════════════════════════════════════════════════════════════════════════════

def viz_fama_french():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    factors = ["Market (β₁)", "SMB (β₂)", "HML (β₃)", "Alpha (α)"]
    values = [3.2, 0.8, -0.5, 1.4]
    colors = [BLU, PUR, NEG, POS]

    fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45],
                        subplot_titles=["Factor Attribution (%)", "Brinson Decomposition"])

    fig.add_trace(go.Bar(
        x=factors, y=values, marker_color=colors,
        text=[f"{v:+.1f}%" for v in values], textposition="outside",
        textfont=dict(color=WHT, size=13),
    ), row=1, col=1)

    # Brinson
    brinson_cats = ["Allocation", "Selection", "Interaction", "Total"]
    brinson_vals = [0.8, 1.4, -0.2, 2.0]
    brinson_colors = [BLU, POS, NEG, ACCENT]
    fig.add_trace(go.Waterfall(
        x=brinson_cats, y=brinson_vals,
        measure=["relative", "relative", "relative", "total"],
        connector=dict(line=dict(color=MUTED)),
        increasing=dict(marker=dict(color=POS)),
        decreasing=dict(marker=dict(color=NEG)),
        totals=dict(marker=dict(color=ACCENT)),
        text=[f"{v:+.1f}%" for v in brinson_vals], textposition="outside",
        textfont=dict(color=WHT),
    ), row=1, col=2)

    fig.update_layout(**dark_layout(
        title="Fama-French 3-Factor + Brinson Attribution", height=450,
    ))
    fig.update_xaxes(gridcolor="#1e1e2e")
    fig.update_yaxes(gridcolor="#1e1e2e")
    fig.write_html(str(OUT / "09_fama_french.html"), include_plotlyjs="cdn")
    print("  ✓ 09_fama_french.html")


# ═════════════════════════════════════════════════════════════════════════════
#  10. DYNAMIC ALLOCATION — Animated Stacked Area
# ═════════════════════════════════════════════════════════════════════════════

def viz_dynamic_allocation():
    import plotly.graph_objects as go

    np.random.seed(5)
    n_days = 300
    assets = ["Equities", "Bonds", "Gold", "Crypto", "Cash"]
    colors_list = [BLU, PUR, GOLD, NEG, POS]

    # Simulate drifting weights
    target = np.array([0.40, 0.25, 0.10, 0.15, 0.10])
    weights = np.zeros((n_days, 5))
    weights[0] = target
    for i in range(1, n_days):
        drift = np.random.normal(0, 0.003, 5)
        weights[i] = np.clip(weights[i - 1] + drift, 0.02, 0.60)
        weights[i] /= weights[i].sum()
        # Rebalance if drift > 5%
        if np.max(np.abs(weights[i] - target)) > 0.05:
            weights[i] = target + np.random.normal(0, 0.005, 5)
            weights[i] = np.clip(weights[i], 0.02, 0.60)
            weights[i] /= weights[i].sum()

    fig = go.Figure()
    for j, (asset, col) in enumerate(zip(assets, colors_list)):
        fig.add_trace(go.Scatter(
            x=np.arange(n_days), y=weights[:, j],
            mode="lines", stackgroup="one", name=asset,
            line=dict(width=0.5, color=col), fillcolor=col.replace(")", ",0.6)") if ")" in col else col,
        ))

    fig.update_layout(**dark_layout(
        title="Dynamic Allocation — Drifting Weights with Rebalance Triggers",
        xaxis_title="Trading Day", yaxis_title="Weight",
        yaxis=dict(range=[0, 1], gridcolor="#1e1e2e"),
    ))
    fig.write_html(str(OUT / "10_dynamic_allocation.html"), include_plotlyjs="cdn")
    print("  ✓ 10_dynamic_allocation.html")


# ═════════════════════════════════════════════════════════════════════════════
#  11. STRESS TESTING — Scenario Comparison Matrix
# ═════════════════════════════════════════════════════════════════════════════

def viz_stress_testing():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    scenarios = ["COVID-19\n(2020)", "GFC\n(2008)", "Rate Hike\n(2022)", "Flash Crash\n(2015)", "Normal"]
    unhedged_dd = [-34, -55, -22, -12, -5]
    hedged_dd = [-12, -18, -9, -5, -3]

    fig = make_subplots(rows=1, cols=2, column_widths=[0.55, 0.45],
                        subplot_titles=["Max Drawdown by Scenario", "Protection Benefit"])

    fig.add_trace(go.Bar(
        x=scenarios, y=unhedged_dd, name="Unhedged",
        marker_color=NEG, opacity=0.7,
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=scenarios, y=hedged_dd, name="BWC Hedged",
        marker_color=POS, opacity=0.9,
    ), row=1, col=1)

    protection = [u - h for u, h in zip(unhedged_dd, hedged_dd)]
    fig.add_trace(go.Bar(
        x=scenarios, y=protection, name="Protection (pp)",
        marker_color=ACCENT,
        text=[f"+{p}pp" for p in protection], textposition="outside",
        textfont=dict(color=WHT),
    ), row=1, col=2)

    fig.update_layout(**dark_layout(
        title="Stress Testing — Historical Shock Scenarios", height=450,
        barmode="group",
    ))
    fig.update_xaxes(gridcolor="#1e1e2e")
    fig.update_yaxes(gridcolor="#1e1e2e")
    fig.write_html(str(OUT / "11_stress_testing.html"), include_plotlyjs="cdn")
    print("  ✓ 11_stress_testing.html")


# ═════════════════════════════════════════════════════════════════════════════
#  12. KELLY CRITERION — Interactive Parabola with Tangent
# ═════════════════════════════════════════════════════════════════════════════

def viz_kelly_criterion():
    import plotly.graph_objects as go

    f = np.linspace(0, 1, 200)
    mu, var = 0.15, 0.20
    g = mu * f - 0.5 * var * f ** 2
    f_star = mu / var

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=f, y=g, mode="lines", line=dict(color=POS, width=3), name="E[log growth]",
    ))
    fig.add_trace(go.Scatter(
        x=[f_star], y=[mu * f_star - 0.5 * var * f_star ** 2],
        mode="markers", marker=dict(size=14, color=ACCENT, symbol="star"),
        name=f"Kelly f* = {f_star:.2f}",
    ))

    # Danger zone
    fig.add_vrect(x0=f_star, x1=1.0, fillcolor=NEG, opacity=0.08, line_width=0)
    fig.add_annotation(x=0.85, y=-0.01, text="Over-leveraged<br>(Ruin Zone)",
                       font=dict(color=NEG, size=12), showarrow=False)

    fig.update_layout(**dark_layout(
        title="Kelly Criterion — Optimal Bet Sizing",
        xaxis_title="Fraction Bet (f)", yaxis_title="E[log(growth)]",
    ))
    fig.write_html(str(OUT / "12_kelly_criterion.html"), include_plotlyjs="cdn")
    print("  ✓ 12_kelly_criterion.html")


# ═════════════════════════════════════════════════════════════════════════════
#  13. YIELD CURVE DYNAMICS — Animated Inversion
# ═════════════════════════════════════════════════════════════════════════════

def viz_yield_curve():
    import plotly.graph_objects as go

    maturities = np.array([0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])

    frames = []
    for blend in np.linspace(0, 1, 60):
        normal = np.array([1.0, 1.3, 1.8, 2.5, 2.9, 3.5, 3.8, 4.2, 4.6, 4.8])
        inverted = np.array([5.2, 5.1, 5.0, 4.8, 4.6, 4.3, 4.1, 3.9, 3.7, 3.6])
        curve = (1 - blend) * normal + blend * inverted

        color = POS if blend < 0.4 else (GOLD if blend < 0.7 else NEG)
        state = "NORMAL" if blend < 0.4 else ("FLATTENING" if blend < 0.7 else "INVERTED")

        frames.append(go.Frame(data=[
            go.Scatter(x=maturities, y=curve, mode="lines+markers",
                       line=dict(color=color, width=3),
                       marker=dict(size=8, color=color),
                       name=f"Yield Curve ({state})"),
        ], name=f"{blend:.2f}"))

    fig = go.Figure(data=frames[0].data, frames=frames)
    fig.update_layout(
        **dark_layout(
            title="Dynamic Yield Curve — Normal → Inverted",
            xaxis_title="Maturity (years)", yaxis_title="Yield (%)",
            xaxis=dict(type="log", gridcolor="#1e1e2e"),
        ),
        updatemenus=[dict(
            type="buttons", showactive=False, x=0.05, y=1.12,
            buttons=[dict(label="▶ Invert", method="animate",
                          args=[None, dict(frame=dict(duration=60, redraw=True), fromcurrent=True)])],
        )],
    )
    fig.write_html(str(OUT / "13_yield_curve.html"), include_plotlyjs="cdn")
    print("  ✓ 13_yield_curve.html")


# ═════════════════════════════════════════════════════════════════════════════
#  14. QUADRATIC VARIATION — Convergence Plot
# ═════════════════════════════════════════════════════════════════════════════

def viz_quadratic_variation():
    import plotly.graph_objects as go

    np.random.seed(42)
    fig = go.Figure()

    configs = [
        (10, NEG, "n=10"), (50, GOLD, "n=50"),
        (200, BLU, "n=200"), (1000, POS, "n=1000"),
    ]

    for n_part, color, label in configs:
        dt = 1.0 / n_part
        qv_avg = np.zeros(n_part)
        for _ in range(100):
            inc = np.random.normal(0, np.sqrt(dt), n_part)
            qv_avg += np.cumsum(inc ** 2)
        qv_avg /= 100
        t_vals = np.linspace(dt, 1.0, n_part)

        step = max(1, n_part // 150)
        fig.add_trace(go.Scatter(
            x=t_vals[::step], y=qv_avg[::step], mode="lines",
            line=dict(color=color, width=2), name=label, opacity=0.85,
        ))

    # Theory line
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1], mode="lines",
        line=dict(color=WHT, width=3, dash="dash"), name="<B>_t = t (theory)",
    ))

    fig.update_layout(**dark_layout(
        title="Quadratic Variation Convergence — <B>_t → t",
        xaxis_title="t", yaxis_title="<B>_t",
    ))
    fig.write_html(str(OUT / "14_quadratic_variation.html"), include_plotlyjs="cdn")
    print("  ✓ 14_quadratic_variation.html")


# ═════════════════════════════════════════════════════════════════════════════
#  15. ALPHA-BETA DECOMPOSITION — Matplotlib Animated
# ═════════════════════════════════════════════════════════════════════════════

def viz_alpha_beta():
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_facecolor("#0a0a0a")
    fig.patch.set_facecolor("#0a0a0a")

    m_vec = np.array([4, 1.5])
    p_vec = np.array([3, 4.5])
    proj = np.dot(p_vec, m_vec) / np.dot(m_vec, m_vec) * m_vec

    ax.annotate("", xy=m_vec, xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=BLU, lw=2.5))
    ax.annotate("", xy=p_vec, xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=POS, lw=2.5))
    ax.annotate("", xy=proj, xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", color=ACCENT, lw=2))
    ax.annotate("", xy=p_vec, xytext=proj,
                arrowprops=dict(arrowstyle="->", color=PUR, lw=2))

    ax.plot(*proj, "o", color=WHT, markersize=6)

    ax.text(m_vec[0] + 0.1, m_vec[1] - 0.3, r"$R_m$ (Market)", color=BLU, fontsize=13)
    ax.text(p_vec[0] + 0.1, p_vec[1] + 0.1, r"$R_p$ (Portfolio)", color=POS, fontsize=13)
    ax.text(proj[0] - 0.5, proj[1] - 0.5, r"$\beta R_m$", color=ACCENT, fontsize=14)
    ax.text((proj[0] + p_vec[0]) / 2 + 0.2, (proj[1] + p_vec[1]) / 2, r"$\alpha$", color=PUR, fontsize=16, weight="bold")

    # Right angle marker
    d1 = (p_vec - proj) / np.linalg.norm(p_vec - proj) * 0.3
    d2 = proj / np.linalg.norm(proj) * 0.3
    sq = plt.Polygon([proj + d1, proj + d1 - d2, proj - d2], fill=False, edgecolor=WHT, linewidth=1)
    ax.add_patch(sq)

    ax.set_xlim(-0.5, 5.5)
    ax.set_ylim(-0.5, 5.5)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.1)
    ax.set_title("Alpha-Beta Orthogonal Decomposition", color=WHT, fontsize=16)
    ax.set_xlabel(r"$x_1$", color=MUTED)
    ax.set_ylabel(r"$x_2$", color=MUTED)

    legend_elements = [
        mpatches.Patch(color=BLU, label="Market Return"),
        mpatches.Patch(color=POS, label="Portfolio Return"),
        mpatches.Patch(color=ACCENT, label="Beta (systematic)"),
        mpatches.Patch(color=PUR, label="Alpha (skill)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", fontsize=11)

    fig.tight_layout()
    fig.savefig(str(OUT / "15_alpha_beta.png"), dpi=200, facecolor="#0a0a0a")
    plt.close(fig)
    print("  ✓ 15_alpha_beta.png")


# ═════════════════════════════════════════════════════════════════════════════
#  16. COVARIANCE HEATMAP — Animated Stress Scenario
# ═════════════════════════════════════════════════════════════════════════════

def viz_correlation_stress():
    import plotly.graph_objects as go

    tickers = ["AAPL", "NVDA", "TSLA", "PLTR", "IONQ", "MSFT", "GOOG", "AMZN"]
    np.random.seed(42)
    normal_corr = np.array([
        [1.0, 0.7, 0.4, 0.5, 0.3, 0.8, 0.75, 0.7],
        [0.7, 1.0, 0.5, 0.6, 0.4, 0.65, 0.6, 0.55],
        [0.4, 0.5, 1.0, 0.6, 0.5, 0.35, 0.3, 0.35],
        [0.5, 0.6, 0.6, 1.0, 0.55, 0.4, 0.35, 0.4],
        [0.3, 0.4, 0.5, 0.55, 1.0, 0.25, 0.2, 0.25],
        [0.8, 0.65, 0.35, 0.4, 0.25, 1.0, 0.85, 0.8],
        [0.75, 0.6, 0.3, 0.35, 0.2, 0.85, 1.0, 0.82],
        [0.7, 0.55, 0.35, 0.4, 0.25, 0.8, 0.82, 1.0],
    ])

    frames = []
    for blend in np.linspace(0, 1, 40):
        stressed = normal_corr * (1 - blend) + blend * (0.15 + 0.85 * np.ones_like(normal_corr))
        np.fill_diagonal(stressed, 1.0)
        state = "Normal" if blend < 0.3 else ("Stress" if blend < 0.7 else "CRISIS: ρ→1")

        frames.append(go.Frame(data=[go.Heatmap(
            z=stressed, x=tickers, y=tickers,
            colorscale=[[0, "#0a0a0a"], [0.5, PUR], [1.0, NEG]],
            zmin=0, zmax=1,
            text=np.round(stressed, 2), texttemplate="%{text:.2f}",
            textfont=dict(size=10, color=WHT),
        )], name=f"{blend:.2f}", layout=dict(title=f"Correlation Matrix — {state}")))

    fig = go.Figure(data=frames[0].data, frames=frames)
    fig.update_layout(
        **dark_layout(title="Correlation Contagion — Normal → Crisis", height=550, width=650),
        updatemenus=[dict(
            type="buttons", showactive=False, x=0.05, y=1.12,
            buttons=[dict(label="▶ Stress", method="animate",
                          args=[None, dict(frame=dict(duration=100, redraw=True), fromcurrent=True)])],
        )],
    )
    fig.write_html(str(OUT / "16_correlation_stress.html"), include_plotlyjs="cdn")
    print("  ✓ 16_correlation_stress.html")


# ═════════════════════════════════════════════════════════════════════════════
#  17. JUMP DIFFUSION — Brownian + Poisson Shocks
# ═════════════════════════════════════════════════════════════════════════════

def viz_jump_diffusion():
    import plotly.graph_objects as go

    np.random.seed(11)
    n, dt = 1000, 0.01
    t = np.linspace(0, n * dt, n)

    # Pure Brownian
    bm = np.cumsum(np.random.normal(0.001, 0.02, n))
    bm = 100 + bm

    # With jumps
    jd = bm.copy()
    jump_times = []
    for i in range(n):
        if np.random.rand() < 0.005:
            jd[i:] -= np.random.uniform(2, 8)
            jump_times.append(i)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=bm, mode="lines", line=dict(color=BLU, width=1.5), name="Pure Brownian", opacity=0.5))
    fig.add_trace(go.Scatter(x=t, y=jd, mode="lines", line=dict(color=NEG, width=2), name="Jump-Diffusion (Merton)"))

    for jt in jump_times:
        fig.add_vline(x=t[jt], line_dash="dot", line_color=ACCENT, opacity=0.4)

    fig.update_layout(**dark_layout(
        title="Merton Jump-Diffusion: dS = μdt + σdW + JdN",
        xaxis_title="Time", yaxis_title="S(t)",
    ))
    fig.write_html(str(OUT / "17_jump_diffusion.html"), include_plotlyjs="cdn")
    print("  ✓ 17_jump_diffusion.html")


# ═════════════════════════════════════════════════════════════════════════════
#  18. RISK DASHBOARD — Comprehensive Subplot Grid
# ═════════════════════════════════════════════════════════════════════════════

def viz_risk_dashboard():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    np.random.seed(42)

    fig = make_subplots(
        rows=3, cols=3, vertical_spacing=0.08, horizontal_spacing=0.08,
        subplot_titles=[
            "Portfolio NAV", "Return Distribution", "Rolling Sharpe (60d)",
            "Sector Weights", "VaR Breach Count", "Correlation Cluster",
            "Drawdown", "Regime Timeline", "Risk Contribution",
        ],
    )

    n = 500
    t = np.arange(n)
    rets = np.random.normal(0.0004, 0.01, n)
    nav = 100 * np.exp(np.cumsum(rets))
    peak = np.maximum.accumulate(nav)
    dd = (nav - peak) / peak

    # 1. NAV
    fig.add_trace(go.Scatter(x=t, y=nav, line=dict(color=POS, width=1.5), showlegend=False), row=1, col=1)

    # 2. Return dist
    fig.add_trace(go.Histogram(x=rets, nbinsx=50, marker_color=BLU, opacity=0.7, showlegend=False), row=1, col=2)

    # 3. Rolling Sharpe
    window = 60
    rolling_sharpe = np.array([
        np.mean(rets[max(0, i - window):i]) / max(np.std(rets[max(0, i - window):i]), 1e-8) * np.sqrt(252)
        for i in range(1, n + 1)
    ])
    fig.add_trace(go.Scatter(x=t, y=rolling_sharpe, line=dict(color=ACCENT, width=1.5), showlegend=False), row=1, col=3)
    fig.add_hline(y=0, line_dash="dash", line_color=MUTED, row=1, col=3)

    # 4. Sector weights pie-style bars
    sectors = ["Tech", "Bonds", "Gold", "Crypto", "Cash"]
    weights = [0.35, 0.30, 0.12, 0.13, 0.10]
    fig.add_trace(go.Bar(x=sectors, y=weights, marker_color=[BLU, PUR, GOLD, NEG, POS], showlegend=False), row=2, col=1)

    # 5. VaR breach histogram
    var_95 = np.percentile(rets, 5)
    breaches = np.array([int(r < var_95) for r in rets])
    monthly_breaches = [np.sum(breaches[i:i + 21]) for i in range(0, n - 21, 21)]
    fig.add_trace(go.Bar(y=monthly_breaches, marker_color=NEG, opacity=0.7, showlegend=False), row=2, col=2)

    # 6. Mini correlation
    mini_corr = np.random.uniform(0.2, 0.9, (5, 5))
    np.fill_diagonal(mini_corr, 1.0)
    mini_corr = (mini_corr + mini_corr.T) / 2
    fig.add_trace(go.Heatmap(z=mini_corr, x=sectors, y=sectors,
                              colorscale=[[0, "#0a0a0a"], [1, PUR]], showscale=False), row=2, col=3)

    # 7. Drawdown
    fig.add_trace(go.Scatter(x=t, y=dd, fill="tozeroy", line=dict(color=NEG, width=1), fillcolor="rgba(255,51,102,0.3)", showlegend=False), row=3, col=1)

    # 8. Regime
    regime_colors_list = [POS if np.random.rand() > 0.3 else (GOLD if np.random.rand() > 0.5 else NEG) for _ in range(n)]
    fig.add_trace(go.Bar(x=t, y=[1]*n, marker_color=regime_colors_list, showlegend=False), row=3, col=2)

    # 9. Risk contribution
    risk_contrib = [0.45, 0.20, 0.08, 0.22, 0.05]
    fig.add_trace(go.Bar(x=sectors, y=risk_contrib, marker_color=[BLU, PUR, GOLD, NEG, POS], showlegend=False), row=3, col=3)

    fig.update_layout(
        **dark_layout(title="BWC Risk Dashboard — 9-Panel Overview", height=900, width=1200),
        showlegend=False,
    )
    for i in range(1, 4):
        for j in range(1, 4):
            fig.update_xaxes(gridcolor="#1e1e2e", row=i, col=j)
            fig.update_yaxes(gridcolor="#1e1e2e", row=i, col=j)
    fig.write_html(str(OUT / "18_risk_dashboard.html"), include_plotlyjs="cdn")
    print("  ✓ 18_risk_dashboard.html")


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN — Generate All
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"Generating visualizations to {OUT}/\n")

    viz_monte_carlo_sde()
    viz_efficient_frontier()
    viz_var_cvar_sweep()
    viz_vol_surface_3d()
    viz_regime_detection()
    viz_black_litterman()
    viz_hrp_clustering()
    viz_backtest_equity()
    viz_fama_french()
    viz_dynamic_allocation()
    viz_stress_testing()
    viz_kelly_criterion()
    viz_yield_curve()
    viz_quadratic_variation()
    viz_alpha_beta()
    viz_correlation_stress()
    viz_jump_diffusion()
    viz_risk_dashboard()

    print(f"\nDone! {len(list(OUT.iterdir()))} files in {OUT}")
