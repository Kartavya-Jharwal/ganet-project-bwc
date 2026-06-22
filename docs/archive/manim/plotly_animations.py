"""
Project BWC — Plotly + Matplotlib Animated Visualizations
Dark theme throughout. Interactive HTML outputs. Advanced statistical viz.
Run: python docs/plotly_animations.py
Outputs to: docs/viz_output/
"""

import numpy as np
from pathlib import Path
from scipy import stats

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
#  MAIN — Generate All
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"Generating visualizations to {OUT}/\n")

    viz_efficient_frontier()
    viz_vol_surface_3d()
    viz_black_litterman()
    viz_backtest_equity()
    viz_fama_french()
    viz_stress_testing()
    viz_kelly_criterion()
    viz_yield_curve()
    viz_quadratic_variation()
    viz_alpha_beta()

    print(f"\nDone! {len(list(OUT.iterdir()))} files in {OUT}")
