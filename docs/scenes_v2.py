"""
Project BWC — Definitive Manim Scenes v2
High-tech deep-learning aesthetic. Sophisticated quant math. No overlaps.
18 scenes covering every model, system component, and mathematical insight.
"""

import numpy as np
from manim import *

# ── Palette ──────────────────────────────────────────────────────────────────
BG = "#050505"
ACCENT = "#eb5e28"
POS = "#00ff88"
NEG = "#ff3366"
MUTED = "#52525b"
WHT = "#f4f4f5"
BLU = "#3b82f6"
PUR = "#8b5cf6"
TEAL = "#14b8a6"
GOLD = "#f59e0b"

config.background_color = BG

# ── Shared Helpers ───────────────────────────────────────────────────────────

def smootherstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (t * 6 - 15) + 10)


class GlowDot(VGroup):
    def __init__(self, point, color=POS, radius=0.06, glow=3.5, **kw):
        super().__init__(**kw)
        self.add(
            Dot(point, radius=radius * glow, color=color, fill_opacity=0.15),
            Dot(point, radius=radius, color=color),
        )


def section_title(text, scene):
    t = Text(text, font_size=30, color=WHT, weight="BOLD").to_corner(UL, buff=0.4)
    scene.play(FadeIn(t, shift=RIGHT * 0.3), run_time=0.6)
    return t


def math_panel(lines, anchor=RIGHT, buff=0.5):
    """Stack of MathTex lines in a bordered box on one side."""
    eqs = VGroup(*[MathTex(l, font_size=22, color=WHT) for l in lines])
    eqs.arrange(DOWN, aligned_edge=LEFT, buff=0.2)
    box = RoundedRectangle(
        corner_radius=0.12,
        width=eqs.width + 0.6,
        height=eqs.height + 0.5,
        color=BLU,
        fill_opacity=0.06,
    )
    grp = VGroup(box, eqs)
    eqs.move_to(box.get_center())
    grp.to_edge(anchor, buff=buff).set_z_index(10)
    return grp


def left_axes(x_range, y_range, x_len=5.5, y_len=3.5):
    return Axes(
        x_range=x_range, y_range=y_range,
        x_length=x_len, y_length=y_len,
        axis_config={"stroke_width": 1.5, "stroke_color": MUTED, "include_numbers": False},
    ).to_edge(LEFT, buff=1.0).shift(DOWN * 0.3)


# ═════════════════════════════════════════════════════════════════════════════
#  1. THE STOCHASTIC VOID — Monte Carlo SDE
# ═════════════════════════════════════════════════════════════════════════════

class Vis_TheStochasticVoid(Scene):
    def construct(self):
        section_title("The Stochastic Void", self)

        panel = math_panel([
            r"dS_t = \mu S_t\,dt + \sigma S_t\,dW_t",
            r"S_T = S_0 \exp\!\Big[\big(\mu - \tfrac{\sigma^2}{2}\big)T + \sigma W_T\Big]",
            r"\text{CVaR}_\alpha = \mathbb{E}[S_T \mid S_T \le \text{VaR}_\alpha]",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([0, 10, 2], [40, 200, 40])
        self.play(Create(axes), run_time=0.7)

        np.random.seed(42)
        paths_grp = VGroup()
        palette = [BLU, PUR, TEAL, ACCENT]

        for i in range(50):
            p = [100.0]
            for _ in range(100):
                p.append(p[-1] * np.exp((0.08 - 0.5 * 0.04) * 0.1 + np.sqrt(0.04) * np.sqrt(0.1) * np.random.normal()))
            xs = np.linspace(0, 10, 101)
            ys = np.clip(p, 40, 200)
            col = palette[i % len(palette)]
            line = axes.plot_line_graph(xs, ys, add_vertex_dots=False, line_color=col)
            line.set_stroke(width=1.2, opacity=0.12 + 0.03 * (i < 5))
            paths_grp.add(line)

        self.play(
            LaggedStart(*[Create(p) for p in paths_grp], lag_ratio=0.01),
            run_time=3, rate_func=rate_functions.ease_out_cubic,
        )

        # Terminal distribution bell at right edge
        terminal_vals = []
        np.random.seed(42)
        for _ in range(2000):
            s = 100.0
            for _ in range(100):
                s *= np.exp((0.08 - 0.5 * 0.04) * 0.1 + np.sqrt(0.04) * np.sqrt(0.1) * np.random.normal())
            terminal_vals.append(s)
        mu_t = np.mean(terminal_vals)
        sig_t = np.std(terminal_vals)

        bell_pts = []
        for y_val in np.linspace(50, 195, 120):
            density = np.exp(-0.5 * ((y_val - mu_t) / sig_t) ** 2) / (sig_t * np.sqrt(2 * np.pi))
            x_screen = axes.c2p(10, y_val)[1]
            bell_pts.append(axes.c2p(10 + density * 400, y_val))
        bell_curve = VMobject().set_points_smoothly(bell_pts).set_color(ACCENT).set_stroke(width=3)
        bell_glow = bell_curve.copy().set_stroke(width=12, opacity=0.2)

        self.play(Create(bell_glow), Create(bell_curve), run_time=1.5)

        # VaR threshold line
        var_5 = np.percentile(terminal_vals, 5)
        var_line = DashedLine(
            axes.c2p(0, var_5), axes.c2p(10, var_5), color=NEG, dash_length=0.15
        ).set_stroke(width=2)
        var_lbl = MathTex(r"\text{VaR}_{5\%}", font_size=18, color=NEG).next_to(var_line, LEFT, buff=0.1)
        self.play(Create(var_line), FadeIn(var_lbl), run_time=0.8)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  2. THE OPTIMAL EDGE — Markowitz Efficient Frontier
# ═════════════════════════════════════════════════════════════════════════════

class Vis_TheOptimalEdge(Scene):
    def construct(self):
        section_title("The Optimal Edge", self)

        panel = math_panel([
            r"\max_{\mathbf{w}}\; \boldsymbol{\mu}^T \mathbf{w} "
            r"- \frac{\lambda}{2}\,\mathbf{w}^T \boldsymbol{\Sigma}\,\mathbf{w}",
            r"\text{s.t.}\;\; \mathbf{1}^T \mathbf{w} = 1,\; w_i \ge 0",
            r"\text{Sharpe} = \frac{\mu_p - r_f}{\sigma_p}",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([0, 0.35, 0.05], [0, 0.20, 0.05])
        self.play(Create(axes), run_time=0.6)

        np.random.seed(99)
        cloud = VGroup()
        for _ in range(400):
            vol = np.random.uniform(0.04, 0.33)
            cap = 0.16 * np.sqrt(max(vol - 0.04, 0) / 0.25)
            if cap > 0.005:
                ret = np.random.uniform(0.005, cap)
                d = Dot(axes.c2p(vol, ret), radius=0.025, color=MUTED, fill_opacity=0.4)
                cloud.add(d)

        self.play(
            LaggedStart(*[FadeIn(d, shift=DOWN * 0.05) for d in cloud], lag_ratio=0.003),
            run_time=1.5,
        )

        frontier = axes.plot(
            lambda x: 0.16 * np.sqrt(max(x - 0.04, 0.0001) / 0.25),
            x_range=[0.04, 0.33], color=POS,
        )
        frontier_glow = frontier.copy().set_stroke(width=14, opacity=0.2)
        self.play(Create(frontier_glow), Create(frontier), run_time=1.5)

        # Tangent portfolio dot
        tang_x, tang_y = 0.12, 0.16 * np.sqrt((0.12 - 0.04) / 0.25)
        tang_dot = GlowDot(axes.c2p(tang_x, tang_y), color=ACCENT, radius=0.07, glow=4)
        tang_lbl = MathTex(r"\mathbf{w}^*", font_size=20, color=ACCENT).next_to(tang_dot, UR, buff=0.1)
        self.play(FadeIn(tang_dot, scale=2), FadeIn(tang_lbl), run_time=0.8)

        # Capital market line from rf to tangent and beyond
        rf_y = 0.02
        slope = (tang_y - rf_y) / tang_x
        cml = axes.plot(lambda x: rf_y + slope * x, x_range=[0, 0.30], color=ACCENT)
        cml.set_stroke(width=2, opacity=0.7)
        self.play(Create(cml), run_time=1.0)

        # Color nearby dots green
        anims = []
        for d in cloud:
            coords = axes.p2c(d.get_center())
            fy = 0.16 * np.sqrt(max(coords[0] - 0.04, 0.0001) / 0.25)
            if fy - coords[1] < 0.012 and coords[0] > 0.05:
                anims.append(d.animate.set_color(POS).set_fill(opacity=0.9).scale(1.4))
        if anims:
            self.play(*anims, run_time=0.8)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  3. ALPHA-BETA ORTHOGONALITY — Factor Decomposition
# ═════════════════════════════════════════════════════════════════════════════

class Vis_AlphaOrthogonality(Scene):
    def construct(self):
        section_title("Alpha-Beta Orthogonality", self)

        panel = math_panel([
            r"R_p = \alpha + \beta\,R_m + \varepsilon",
            r"\beta = \frac{\text{Cov}(R_p, R_m)}{\text{Var}(R_m)}",
            r"\alpha = R_p - \beta\,R_m \;\perp\; R_m",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        plane = NumberPlane(
            x_range=[-0.5, 5.5], y_range=[-0.5, 5.5],
            x_length=5.5, y_length=5.5,
            background_line_style={"stroke_opacity": 0.08, "stroke_color": BLU},
        ).to_edge(LEFT, buff=0.8).shift(DOWN * 0.2)
        self.play(FadeIn(plane), run_time=0.5)

        # Market vector
        v_market = Arrow(
            plane.c2p(0, 0), plane.c2p(4, 1.5),
            color=BLU, buff=0, stroke_width=5,
        )
        lbl_m = MathTex(r"R_m", font_size=22, color=BLU).next_to(v_market, DOWN, buff=0.1)

        # Portfolio vector
        v_port = Arrow(
            plane.c2p(0, 0), plane.c2p(3, 4.5),
            color=POS, buff=0, stroke_width=5,
        )
        lbl_p = MathTex(r"R_p", font_size=22, color=POS).next_to(v_port, LEFT, buff=0.1)

        self.play(GrowArrow(v_market), FadeIn(lbl_m), run_time=0.7)
        self.play(GrowArrow(v_port), FadeIn(lbl_p), run_time=0.7)

        # Projection (beta component)
        m_vec = np.array([4, 1.5])
        p_vec = np.array([3, 4.5])
        proj_scalar = np.dot(p_vec, m_vec) / np.dot(m_vec, m_vec)
        proj_pt = proj_scalar * m_vec

        v_beta = Arrow(
            plane.c2p(0, 0), plane.c2p(*proj_pt),
            color=ACCENT, buff=0, stroke_width=4,
        )
        lbl_beta = MathTex(r"\beta R_m", font_size=20, color=ACCENT).next_to(v_beta.get_end(), DOWN, buff=0.15)

        # Alpha component (orthogonal)
        v_alpha = Arrow(
            plane.c2p(*proj_pt), plane.c2p(3, 4.5),
            color=PUR, buff=0, stroke_width=4,
        )
        lbl_alpha = MathTex(r"\alpha", font_size=22, color=PUR).next_to(v_alpha, RIGHT, buff=0.1)

        # Right angle marker
        corner_size = 0.25
        right_angle = VMobject()
        rp = plane.c2p(*proj_pt)
        right_angle.set_points_as_corners([
            rp + corner_size * (plane.c2p(3, 4.5) - rp) / np.linalg.norm(plane.c2p(3, 4.5) - rp),
            rp + corner_size * (plane.c2p(3, 4.5) - rp) / np.linalg.norm(plane.c2p(3, 4.5) - rp)
              + corner_size * (plane.c2p(*proj_pt) - plane.c2p(0, 0)) / max(np.linalg.norm(plane.c2p(*proj_pt) - plane.c2p(0, 0)), 0.01) * (-1),
            rp,
        ])
        right_angle.set_stroke(WHT, width=1.5)

        self.play(GrowArrow(v_beta), FadeIn(lbl_beta), run_time=0.8)
        self.play(GrowArrow(v_alpha), FadeIn(lbl_alpha), Create(right_angle), run_time=0.8)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  4. VaR RISK SWEEP — Gaussian Tail + CVaR
# ═════════════════════════════════════════════════════════════════════════════

class Vis_VaRRiskSweep(Scene):
    def construct(self):
        section_title("Value-at-Risk Sweep", self)

        panel = math_panel([
            r"\text{VaR}_\alpha = \mu + z_\alpha\,\sigma",
            r"\text{CVaR}_\alpha = \mu - \sigma\,\frac{\phi(z_\alpha)}{1-\alpha}",
            r"z_{\text{CF}} = z + \tfrac{z^2-1}{6}S + \tfrac{z^3-3z}{24}K",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([-4.5, 4.5, 1], [0, 0.45, 0.1], x_len=5.5, y_len=3.8)
        self.play(Create(axes), run_time=0.6)

        gauss = axes.plot(
            lambda x: np.exp(-0.5 * x ** 2) / np.sqrt(2 * np.pi),
            x_range=[-4.2, 4.2], color=WHT, stroke_width=2,
        )
        self.play(Create(gauss), run_time=1.2)

        # Riemann rectangles morphing to smooth area
        rects = axes.get_riemann_rectangles(
            gauss, x_range=[-4.2, -1.645], dx=0.3,
            color=ACCENT, fill_opacity=0.5, stroke_width=0.5,
        )
        self.play(Create(rects), run_time=1.5)

        smooth_area = axes.get_area(gauss, x_range=[-4.2, -1.645], color=NEG, opacity=0.65)
        self.play(Transform(rects, smooth_area), run_time=1.5)

        # VaR line
        var_x = -1.645
        var_height = np.exp(-0.5 * var_x ** 2) / np.sqrt(2 * np.pi)
        var_line = DashedLine(
            axes.c2p(var_x, 0), axes.c2p(var_x, var_height),
            color=NEG, dash_length=0.1,
        ).set_stroke(width=2.5)
        var_lbl = MathTex(r"\text{VaR}_{95\%}", font_size=16, color=NEG).next_to(
            axes.c2p(var_x, var_height), UP, buff=0.1
        )
        self.play(Create(var_line), FadeIn(var_lbl), run_time=0.7)

        # CVaR marker deeper in the tail
        cvar_x = -2.06
        cvar_dot = GlowDot(axes.c2p(cvar_x, 0), color=ACCENT, radius=0.08, glow=4)
        cvar_lbl = MathTex(r"\text{CVaR}", font_size=16, color=ACCENT).next_to(cvar_dot, DOWN, buff=0.15)
        self.play(FadeIn(cvar_dot, scale=2), FadeIn(cvar_lbl), run_time=0.7)

        # Animate a sweep of the VaR threshold
        tracker = ValueTracker(-1.645)

        moving_line = always_redraw(lambda: DashedLine(
            axes.c2p(tracker.get_value(), 0),
            axes.c2p(tracker.get_value(), max(np.exp(-0.5 * tracker.get_value() ** 2) / np.sqrt(2 * np.pi), 0.01)),
            color=GOLD, dash_length=0.08,
        ).set_stroke(width=2))
        self.add(moving_line)
        self.play(tracker.animate.set_value(-2.33), run_time=2, rate_func=rate_functions.ease_in_out_sine)
        self.play(tracker.animate.set_value(-1.28), run_time=2, rate_func=rate_functions.ease_in_out_sine)

        self.wait(1.5)


# ═════════════════════════════════════════════════════════════════════════════
#  5. MONTE CARLO INSIGHTS — Quadratic Variation Convergence
# ═════════════════════════════════════════════════════════════════════════════

class Vis_MonteCarloInsights(Scene):
    def construct(self):
        section_title("Monte Carlo: Quadratic Variation", self)

        panel = math_panel([
            r"\langle B \rangle_t = t",
            r"\sum_{i}\!\left(B_{t_{i+1}} - B_{t_i}\right)^2 \xrightarrow{n\to\infty} t",
            r"\text{Partition refinement } \Delta t = T/n",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([0, 1.05, 0.2], [0, 1.6, 0.4], x_len=5.5, y_len=4.0)
        self.play(Create(axes), run_time=0.6)

        # Theory line
        theory = axes.plot(lambda t: t, x_range=[0, 1.0], color=WHT)
        theory.set_stroke(width=3, opacity=0.6)
        theory_lbl = MathTex(r"\langle B\rangle_t = t", font_size=16, color=WHT).next_to(
            axes.c2p(0.85, 0.85), UL, buff=0.1
        )
        self.play(Create(theory), FadeIn(theory_lbl), run_time=0.8)

        configs = [
            (10, NEG, "n=10"),
            (50, GOLD, "n=50"),
            (200, BLU, "n=200"),
            (1000, POS, "n=1000"),
        ]

        np.random.seed(42)
        legend = VGroup()

        for n_part, color, label in configs:
            dt = 1.0 / n_part
            qv_avg = np.zeros(n_part)
            for _ in range(80):
                inc = np.random.normal(0, np.sqrt(dt), n_part)
                qv_avg += np.cumsum(inc ** 2)
            qv_avg /= 80

            step = max(1, n_part // 80)
            t_plot = np.linspace(dt, 1.0, n_part)[::step]
            qv_plot = qv_avg[::step]

            graph = axes.plot_line_graph(
                t_plot, qv_plot, add_vertex_dots=False, line_color=color,
            ).set_stroke(width=2.5, opacity=0.85)
            self.play(Create(graph), run_time=0.6)

            leg = VGroup(
                Dot(color=color, radius=0.05),
                Text(label, font_size=13, color=color),
            ).arrange(RIGHT, buff=0.1)
            legend.add(leg)

        legend.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        legend.next_to(axes, DOWN, buff=0.25).align_to(axes, LEFT)
        self.play(FadeIn(legend), run_time=0.5)

        conv = Text("Finer partitions converge to t", font_size=14, color=POS)
        conv.next_to(legend, RIGHT, buff=0.5)
        self.play(FadeIn(conv, shift=UP * 0.15), run_time=0.5)
        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  6. REGIME PHASE SHIFT — Market State Collapse
# ═════════════════════════════════════════════════════════════════════════════

class Vis_RegimePhaseShift(Scene):
    def construct(self):
        section_title("Regime Phase Shift", self)

        panel = math_panel([
            r"n_{\text{crisis}} \ge 3 \implies \text{CRISIS}",
            r"n_{\text{crisis}} \ge 1 \implies \text{TRANSITION}",
            r"\rho_{ij} \to 1 \;\text{under stress}",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([0, 10, 2], [40, 180, 40], x_len=5.5, y_len=3.8)
        self.play(Create(axes), run_time=0.6)

        # Normal regime
        x1 = np.linspace(0, 5, 120)
        y1 = 100 + x1 * 6 + np.sin(x1 * 3) * 8
        normal = axes.plot_line_graph(x1, y1, add_vertex_dots=False, line_color=BLU)
        normal.set_stroke(width=3)
        self.play(Create(normal), run_time=1.5, rate_func=linear)

        # Shock event
        shock = DashedLine(
            axes.c2p(5, 40), axes.c2p(5, 180), color=NEG, dash_length=0.12
        ).set_stroke(width=2.5)
        shock_lbl = MathTex(r"\text{Regime Break}", font_size=18, color=NEG).next_to(
            axes.c2p(5, 170), RIGHT, buff=0.15
        )

        self.play(
            Create(shock), FadeIn(shock_lbl, shift=LEFT * 0.2),
            run_time=0.6, rate_func=rate_functions.ease_out_bounce,
        )

        # Crash path
        x2 = np.linspace(5, 10, 120)
        np.random.seed(7)
        y2_crash = y1[-1] - (x2 - 5) * 18 + np.random.normal(0, 12, 120)
        crash = axes.plot_line_graph(x2, np.clip(y2_crash, 40, 180), add_vertex_dots=False, line_color=NEG)
        crash.set_stroke(width=2.5)
        self.play(Create(crash), run_time=1.2, rate_func=rate_functions.ease_in_cubic)

        # BWC alpha path surviving
        y2_bwc = y1[-1] + (x2 - 5) * 3 + np.sin(x2 * 3) * 4
        bwc = axes.plot_line_graph(x2, np.clip(y2_bwc, 40, 180), add_vertex_dots=False, line_color=POS)
        bwc.set_stroke(width=4.5)
        bwc_glow = bwc.copy().set_stroke(width=14, opacity=0.2)

        self.play(
            FadeOut(crash, run_time=0.5),
            Create(bwc_glow), Create(bwc),
            run_time=1.5, rate_func=rate_functions.ease_in_out_sine,
        )

        # Labels
        lbl_crash = Text("Unhedged", font_size=13, color=NEG).next_to(axes.c2p(9, 50), UP, buff=0.1)
        lbl_bwc = Text("BWC Hedged", font_size=13, color=POS).next_to(axes.c2p(9, 145), UP, buff=0.1)
        self.play(FadeIn(lbl_bwc), run_time=0.4)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  7. INVARIANT BALANCING — HRP Recursive Bisection
# ═════════════════════════════════════════════════════════════════════════════

class Vis_InvariantBalancing(Scene):
    def construct(self):
        section_title("Invariant Balancing: HRP", self)

        panel = math_panel([
            r"D_{ij} = \sqrt{\tfrac{1}{2}(1 - \rho_{ij})}",
            r"\alpha = 1 - \frac{\sigma^2_{c_0}}{\sigma^2_{c_0} + \sigma^2_{c_1}}",
            r"w_i = \frac{1/\sigma_i^2}{\sum_j 1/\sigma_j^2}",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        # Dendrogram-style tree
        root = np.array([-2.0, 2.8, 0])
        l1_left = root + np.array([-2.0, -1.2, 0])
        l1_right = root + np.array([2.0, -1.2, 0])

        l2_ll = l1_left + np.array([-1.0, -1.2, 0])
        l2_lr = l1_left + np.array([1.0, -1.2, 0])
        l2_rl = l1_right + np.array([-1.0, -1.2, 0])
        l2_rr = l1_right + np.array([1.0, -1.2, 0])

        # Asset labels at leaves
        assets = ["AAPL", "NVDA", "TSLA", "PLTR"]
        leaf_positions = [l2_ll, l2_lr, l2_rl, l2_rr]
        vols = [0.28, 0.35, 0.52, 0.61]
        leaf_colors = [BLU, BLU, PUR, PUR]

        # Draw tree edges
        edges = [
            (root, l1_left), (root, l1_right),
            (l1_left, l2_ll), (l1_left, l2_lr),
            (l1_right, l2_rl), (l1_right, l2_rr),
        ]
        edge_mobs = VGroup()
        for s, e in edges:
            line = Line(s, e, color=MUTED, stroke_width=2)
            edge_mobs.add(line)
        self.play(LaggedStart(*[Create(e) for e in edge_mobs], lag_ratio=0.1), run_time=1.0)

        # Nodes
        root_dot = GlowDot(root, color=ACCENT, radius=0.1, glow=3)
        mid_dots = VGroup(
            GlowDot(l1_left, color=BLU, radius=0.08),
            GlowDot(l1_right, color=PUR, radius=0.08),
        )
        self.play(FadeIn(root_dot), FadeIn(mid_dots), run_time=0.5)

        # Leaf asset boxes
        leaf_grp = VGroup()
        for pos, name, vol, col in zip(leaf_positions, assets, vols, leaf_colors):
            box = RoundedRectangle(
                width=1.2, height=0.7, corner_radius=0.08, color=col, fill_opacity=0.15,
            ).move_to(pos)
            txt = Text(name, font_size=14, color=WHT).move_to(box.get_center() + UP * 0.12)
            vtxt = MathTex(rf"\sigma={vol}", font_size=12, color=col).move_to(box.get_center() + DOWN * 0.15)
            leaf_grp.add(VGroup(box, txt, vtxt))

        self.play(LaggedStart(*[FadeIn(l, scale=0.8) for l in leaf_grp], lag_ratio=0.12), run_time=0.8)

        # Animate weight allocation flowing down
        alpha_lbl = MathTex(r"\alpha=0.62", font_size=16, color=ACCENT).next_to(root_dot, UP, buff=0.2)
        self.play(FadeIn(alpha_lbl), run_time=0.4)

        w_left = MathTex(r"w=0.62", font_size=14, color=BLU).next_to(mid_dots[0], LEFT, buff=0.15)
        w_right = MathTex(r"w=0.38", font_size=14, color=PUR).next_to(mid_dots[1], RIGHT, buff=0.15)
        self.play(FadeIn(w_left), FadeIn(w_right), run_time=0.5)

        # Pulse particles down the tree
        for start, end in [(root, l1_left), (root, l1_right), (l1_left, l2_ll), (l1_left, l2_lr), (l1_right, l2_rl), (l1_right, l2_rr)]:
            pkt = Dot(start, radius=0.05, color=POS)
            self.play(pkt.animate.move_to(end), run_time=0.25, rate_func=smootherstep)
            self.play(FadeOut(pkt), run_time=0.08)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  8. STRUCTURAL DATA FLOW — Pipeline Lattice
# ═════════════════════════════════════════════════════════════════════════════

class Vis_StructuralDataFlow(Scene):
    def construct(self):
        section_title("Structural Data Flow", self)

        panel = math_panel([
            r"\text{Raw} \xrightarrow{\text{parse}} \text{Features} "
            r"\xrightarrow{\Sigma^{-1}} \text{Signals}",
            r"\text{DuckDB}: O(\log n)\;\text{columnar lookups}",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        # Scattered entropy dots (raw web data)
        np.random.seed(4)
        chaos = VGroup(*[
            Dot(
                np.array([-5.5 + np.random.uniform(0, 2.5), np.random.uniform(-2, 2.5), 0]),
                color=MUTED, radius=0.06,
            ) for _ in range(36)
        ])
        self.play(FadeIn(chaos, shift=RIGHT * 0.15, lag_ratio=0.03), run_time=1.0)

        # DuckDB lattice rectangle
        db = Rectangle(width=2.2, height=3.0, color=BLU, fill_opacity=0.08, stroke_width=2)
        db.move_to(np.array([-1.0, 0.3, 0]))
        db_lbl = Text("DuckDB", font_size=16, color=BLU, weight="BOLD").next_to(db, DOWN, buff=0.15)
        self.play(Create(db), FadeIn(db_lbl), run_time=0.6)

        # Snap particles into grid inside DB
        grid_pts = []
        for r in range(6):
            for c in range(6):
                grid_pts.append(db.get_corner(UL) + RIGHT * (0.18 + c * 0.36) + DOWN * (0.2 + r * 0.48))

        snap_anims = []
        for i, dot in enumerate(chaos):
            target = Dot(grid_pts[i], color=POS, radius=0.05)
            snap_anims.append(Transform(dot, target))
        self.play(*snap_anims, run_time=1.0, rate_func=rate_functions.ease_in_out_back)

        # Feature engine triangle
        feat = Polygon(
            UP * 0.6, LEFT * 0.6, RIGHT * 0.6,
            color=PUR, fill_opacity=0.2, stroke_width=2,
        ).scale(1.3).move_to(np.array([2.0, 0.3, 0])).rotate(-PI / 2)
        feat_lbl = Text("Features", font_size=14, color=PUR).next_to(feat, DOWN, buff=0.15)
        self.play(FadeIn(feat, scale=0.8), FadeIn(feat_lbl), run_time=0.5)

        # Vector flowing from DB to features
        vec = Rectangle(width=1.6, height=0.25, color=POS, fill_opacity=0.85)
        vec.move_to(db.get_center())
        self.play(FadeOut(chaos), FadeIn(vec), run_time=0.5)
        self.play(
            vec.animate.move_to(feat.get_center()).scale(0.6).set_color(PUR),
            run_time=0.8, rate_func=rate_functions.ease_in_out_sine,
        )

        # Agent node
        agent = Circle(radius=0.5, color=ACCENT, fill_opacity=0.15, stroke_width=2)
        agent.move_to(np.array([2.0, -2.0, 0]))
        agent_lbl = Text("Agent", font_size=14, color=ACCENT).move_to(agent.get_center())
        arrow_fa = Arrow(feat.get_bottom(), agent.get_top(), color=ACCENT, stroke_width=2, buff=0.1)
        self.play(FadeIn(agent), FadeIn(agent_lbl), GrowArrow(arrow_fa), run_time=0.6)

        # Signal pulse
        pulse = GlowDot(agent.get_center(), color=ACCENT, radius=0.12, glow=5)
        self.play(FadeIn(pulse, scale=3), run_time=0.5)
        self.play(FadeOut(pulse), run_time=0.3)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  9. FAMA-FRENCH ATTRIBUTION
# ═════════════════════════════════════════════════════════════════════════════

class Vis_FamaFrenchAttribution(Scene):
    def construct(self):
        section_title("Fama-French Attribution", self)

        panel = math_panel([
            r"R_p - R_f = \alpha + \beta_1(R_m - R_f) + \beta_2\,\text{SMB}",
            r"+ \beta_3\,\text{HML} + \varepsilon",
            r"R_a = \sum_i (w_i^P - w_i^B)(r_i^B - r^B)",
            r"+ \sum_i w_i^B(r_i^P - r_i^B)",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([-0.5, 4.5, 1], [-0.02, 0.05, 0.01], x_len=5.0, y_len=3.5)
        self.play(Create(axes), run_time=0.5)

        factors = ["Market", "SMB", "HML", "Alpha"]
        values = [0.032, 0.008, -0.005, 0.014]
        colors = [BLU, PUR, NEG, POS]

        bars = VGroup()
        labels = VGroup()
        for i, (name, val, col) in enumerate(zip(factors, values, colors)):
            h = abs(axes.c2p(0, val)[1] - axes.c2p(0, 0)[1])
            bar = Rectangle(
                width=0.8, height=h, color=col, fill_opacity=0.85, stroke_width=1,
            )
            if val >= 0:
                bar.move_to(axes.c2p(i, val / 2))
            else:
                bar.move_to(axes.c2p(i, val / 2))
            bars.add(bar)

            lbl = Text(name, font_size=12, color=WHT).next_to(axes.c2p(i, -0.02), DOWN, buff=0.08)
            val_lbl = Text(f"{val:+.1%}", font_size=14, color=col).next_to(bar, UP if val >= 0 else DOWN, buff=0.08)
            labels.add(VGroup(lbl, val_lbl))

        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.15),
            run_time=1.5,
        )
        self.play(FadeIn(labels), run_time=0.6)

        # Highlight alpha bar with glow
        alpha_glow = bars[3].copy().set_fill(opacity=0).set_stroke(color=POS, width=6, opacity=0.4)
        self.play(FadeIn(alpha_glow), run_time=0.5)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  10. BACKTEST ENGINE — Walk-Forward Equity Curve
# ═════════════════════════════════════════════════════════════════════════════

class Vis_BacktestEngine(Scene):
    def construct(self):
        section_title("Backtest Engine", self)

        panel = math_panel([
            r"\text{Sharpe} = \frac{(\mu - r_f)}{\sigma}\,\sqrt{252}",
            r"\text{Sortino} = \frac{\mu - r_f}{\sigma_{\text{down}}}",
            r"\text{Drawdown} = \frac{\text{peak} - \text{NAV}}{\text{peak}}",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([0, 6, 1], [80, 260, 40], x_len=5.5, y_len=3.5)
        x_lbl = Text("Year", font_size=12, color=MUTED).next_to(axes, DOWN, buff=0.2)
        self.play(Create(axes), FadeIn(x_lbl), run_time=0.6)

        t = np.linspace(0, 6, 150)
        bench = 100 * np.exp(0.07 * t)
        np.random.seed(3)
        bwc_raw = 100 * np.exp(0.14 * t + 0.02 * np.sin(t * 5))

        bench_line = axes.plot_line_graph(t, bench, add_vertex_dots=False, line_color=MUTED)
        bench_line.set_stroke(width=2.5, opacity=0.6)
        bwc_line = axes.plot_line_graph(t, bwc_raw, add_vertex_dots=False, line_color=POS)
        bwc_line.set_stroke(width=4)
        bwc_glow = bwc_line.copy().set_stroke(width=14, opacity=0.15)

        self.play(Create(bench_line), run_time=1.5)
        self.play(Create(bwc_glow), Create(bwc_line), run_time=2.0, rate_func=rate_functions.ease_in_out_sine)

        # Outperformance shaded area
        area = axes.get_area(
            axes.plot(lambda x: 100 * np.exp(0.14 * x + 0.02 * np.sin(x * 5)), x_range=[0, 6]),
            bounded_graph=axes.plot(lambda x: 100 * np.exp(0.07 * x), x_range=[0, 6]),
            color=POS, opacity=0.1,
        )
        self.play(FadeIn(area), run_time=0.6)

        # Walk-forward windows (vertical dashed lines)
        for yr in [1, 2, 3, 4, 5]:
            wf = DashedLine(axes.c2p(yr, 80), axes.c2p(yr, 260), color=MUTED, dash_length=0.08)
            wf.set_stroke(width=1, opacity=0.3)
            self.play(Create(wf), run_time=0.15)

        # Metrics readout
        metrics = VGroup(
            MathTex(r"\text{Sharpe: } 1.47", font_size=16, color=POS),
            MathTex(r"\text{CAGR: } 14.8\%", font_size=16, color=BLU),
            MathTex(r"\text{Max DD: } -8.3\%", font_size=16, color=NEG),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        metrics.next_to(axes, DOWN, buff=0.5).align_to(axes, LEFT)
        self.play(Write(metrics), run_time=0.8)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  11. AGENT OPTIMIZER — Black-Litterman Convergence
# ═════════════════════════════════════════════════════════════════════════════

class Vis_AgentOptimizer(Scene):
    def construct(self):
        section_title("Agent Optimizer: Black-Litterman", self)

        panel = math_panel([
            r"\boldsymbol{\Pi} = \delta\,\boldsymbol{\Sigma}\,\mathbf{w}_{\text{mkt}}",
            r"\mathbf{E}[R] = [(\tau\Sigma)^{-1} + P^T\Omega^{-1}P]^{-1}",
            r"\cdot [(\tau\Sigma)^{-1}\Pi + P^T\Omega^{-1}Q]",
            r"\mathbf{w}^* = \arg\max\;\mu^T w - \frac{\lambda}{2}w^T\Sigma w",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        # Convergence visualization: prior -> posterior shift
        axes = left_axes([-0.05, 0.25, 0.05], [0, 12, 3], x_len=5.0, y_len=3.5)
        x_lbl = MathTex(r"\mathbb{E}[R]", font_size=16, color=MUTED).next_to(axes, DOWN, buff=0.2)
        self.play(Create(axes), FadeIn(x_lbl), run_time=0.6)

        # Prior distribution (market-implied)
        prior_mu, prior_sig = 0.08, 0.04
        prior_curve = axes.plot(
            lambda x: 10 * np.exp(-0.5 * ((x - prior_mu) / prior_sig) ** 2),
            x_range=[0, 0.22], color=BLU,
        )
        prior_curve.set_stroke(width=3)
        prior_lbl = MathTex(r"\Pi\;\text{(prior)}", font_size=14, color=BLU).next_to(
            axes.c2p(prior_mu, 10.5), UP, buff=0.1
        )
        self.play(Create(prior_curve), FadeIn(prior_lbl), run_time=1.0)

        # View distribution
        view_mu, view_sig = 0.15, 0.03
        view_curve = axes.plot(
            lambda x: 8 * np.exp(-0.5 * ((x - view_mu) / view_sig) ** 2),
            x_range=[0.02, 0.22], color=GOLD,
        )
        view_curve.set_stroke(width=2.5, opacity=0.7)
        view_lbl = MathTex(r"Q\;\text{(views)}", font_size=14, color=GOLD).next_to(
            axes.c2p(view_mu, 8.5), UP, buff=0.1
        )
        self.play(Create(view_curve), FadeIn(view_lbl), run_time=0.8)

        # Posterior (blend) — animated morphing
        post_mu = 0.11
        post_sig = 0.025
        posterior = axes.plot(
            lambda x: 11 * np.exp(-0.5 * ((x - post_mu) / post_sig) ** 2),
            x_range=[0, 0.22], color=POS,
        )
        posterior.set_stroke(width=4)
        post_glow = posterior.copy().set_stroke(width=14, opacity=0.2)
        post_lbl = MathTex(r"\mathbb{E}[R]\;\text{(posterior)}", font_size=14, color=POS).next_to(
            axes.c2p(post_mu, 11.5), UP, buff=0.1
        )

        self.play(
            Create(post_glow), Create(posterior), FadeIn(post_lbl),
            prior_curve.animate.set_stroke(opacity=0.3),
            view_curve.animate.set_stroke(opacity=0.3),
            run_time=1.5, rate_func=rate_functions.ease_in_out_sine,
        )

        # Optimal weight bar
        w_bar = Rectangle(width=3.0, height=0.3, color=ACCENT, fill_opacity=0.8)
        w_bar.next_to(axes, DOWN, buff=0.8).align_to(axes, LEFT)
        w_lbl = MathTex(r"\mathbf{w}^*\;\text{allocation}", font_size=14, color=ACCENT).next_to(w_bar, RIGHT, buff=0.15)
        self.play(GrowFromEdge(w_bar, LEFT), FadeIn(w_lbl), run_time=0.8)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  12. MATRIX ARCHITECTURE — Digital Rain + System Graph
# ═════════════════════════════════════════════════════════════════════════════

class Vis_MatrixArchitecture(Scene):
    def construct(self):
        section_title("The Architecture Matrix", self)

        # Digital rain background (columns of falling characters)
        np.random.seed(42)
        rain_chars = VGroup()
        char_set = "01ABCDEF"
        for col in range(28):
            x = -6.5 + col * 0.5
            n_chars = np.random.randint(4, 12)
            start_y = np.random.uniform(1, 4)
            for row in range(n_chars):
                ch = Text(
                    str(np.random.choice(list(char_set))),
                    font_size=12, color=POS, font="monospace",
                )
                ch.set_opacity(0.06 + 0.04 * (row == 0))
                ch.move_to(np.array([x, start_y - row * 0.35, 0]))
                rain_chars.add(ch)

        self.play(FadeIn(rain_chars, lag_ratio=0.002), run_time=1.5)
        self.play(rain_chars.animate.shift(DOWN * 2).set_opacity(0.03), run_time=2, rate_func=linear)

        # Architecture nodes
        nodes_data = [
            ("Spiders", [-4.0, 1.8, 0], BLU),
            ("FRED API", [-4.0, 0.2, 0], TEAL),
            ("DuckDB", [-1.2, 1.0, 0], PUR),
            ("Features", [1.2, 1.8, 0], BLU),
            ("Macro Model", [1.2, -0.2, 0], GOLD),
            ("Optimizer", [3.8, 1.0, 0], ACCENT),
            ("Risk Mgr", [3.8, -1.2, 0], NEG),
            ("Backtest", [1.2, -2.0, 0], POS),
            ("Dashboard", [3.8, -2.8, 0], WHT),
        ]

        node_mobs = {}
        for name, pos, col in nodes_data:
            bg = RoundedRectangle(
                width=1.6, height=0.55, corner_radius=0.08,
                color=col, fill_opacity=0.12, stroke_width=1.5,
            ).move_to(pos)
            lbl = Text(name, font_size=12, color=WHT, weight="BOLD").move_to(bg.get_center())
            grp = VGroup(bg, lbl)
            node_mobs[name] = grp

        self.play(
            LaggedStart(*[FadeIn(n, scale=0.85) for n in node_mobs.values()], lag_ratio=0.08),
            run_time=1.5,
        )

        # Directed edges
        edges = [
            ("Spiders", "DuckDB"), ("FRED API", "DuckDB"),
            ("DuckDB", "Features"), ("DuckDB", "Macro Model"),
            ("Features", "Optimizer"), ("Macro Model", "Optimizer"),
            ("Optimizer", "Risk Mgr"), ("Optimizer", "Backtest"),
            ("Risk Mgr", "Dashboard"), ("Backtest", "Dashboard"),
        ]
        arrows = VGroup()
        for src, dst in edges:
            s = node_mobs[src]
            d = node_mobs[dst]
            a = Arrow(
                s.get_center(), d.get_center(),
                buff=0.45, color=MUTED, stroke_width=1.5, tip_length=0.12,
            )
            arrows.add(a)

        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.06),
            run_time=1.5,
        )

        # Data packet traversal
        flow_path = ["Spiders", "DuckDB", "Features", "Optimizer", "Risk Mgr", "Dashboard"]
        pkt = GlowDot(node_mobs[flow_path[0]].get_center(), color=POS, radius=0.08, glow=4)
        self.add(pkt)
        for i in range(len(flow_path) - 1):
            self.play(
                pkt.animate.move_to(node_mobs[flow_path[i + 1]].get_center()),
                run_time=0.35, rate_func=smootherstep,
            )
        self.play(FadeOut(pkt), run_time=0.2)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  13. WEB SPIDERS — Radial Crawl Graph
# ═════════════════════════════════════════════════════════════════════════════

class Vis_WebSpiders(Scene):
    def construct(self):
        section_title("Web Spiders: Data Harvest", self)

        panel = math_panel([
            r"\text{Throughput} = \min(R_{\text{req}},\; R_{\text{limit}})",
            r"\text{Backoff}: t_{n+1} = 2^n \cdot t_0",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        center = np.array([-1.5, 0.0, 0])
        spider = Circle(radius=0.5, color=ACCENT, fill_opacity=0.2, stroke_width=2).move_to(center)
        spider_lbl = Text("Scrapy", font_size=14, color=ACCENT, weight="BOLD").move_to(spider.get_center())
        self.play(FadeIn(spider), FadeIn(spider_lbl), run_time=0.5)

        # Radial source nodes
        sources = [
            ("yfinance", 2.2, 60, BLU),
            ("FRED", 2.2, 130, TEAL),
            ("Massive", 2.5, 200, PUR),
            ("EDGAR", 2.2, 270, GOLD),
            ("News RSS", 2.5, 330, NEG),
        ]

        src_mobs = []
        for name, dist, angle_deg, col in sources:
            angle = angle_deg * DEGREES
            pos = center + dist * np.array([np.cos(angle), np.sin(angle), 0])
            box = RoundedRectangle(
                width=1.3, height=0.5, corner_radius=0.06,
                color=col, fill_opacity=0.12, stroke_width=1.5,
            ).move_to(pos)
            txt = Text(name, font_size=12, color=WHT).move_to(box.get_center())
            grp = VGroup(box, txt)
            src_mobs.append(grp)

        self.play(
            LaggedStart(*[FadeIn(s, shift=OUT * 0.1) for s in src_mobs], lag_ratio=0.1),
            run_time=1.0,
        )

        # Web lines (spider silk)
        web_lines = VGroup()
        for src in src_mobs:
            line = Line(
                spider.get_center(), src.get_center(),
                color=MUTED, stroke_width=1,
            )
            web_lines.add(line)
        self.play(Create(web_lines), run_time=0.6)

        # Animated data packets flowing inward
        for _ in range(2):
            pkts = []
            for src, line in zip(src_mobs, web_lines):
                pkt = Dot(src.get_center(), radius=0.04, color=POS, fill_opacity=0.8)
                pkts.append(pkt)
            self.play(*[FadeIn(p) for p in pkts], run_time=0.1)
            self.play(
                *[p.animate.move_to(spider.get_center()) for p in pkts],
                run_time=0.5, rate_func=smootherstep,
            )
            self.play(*[FadeOut(p) for p in pkts], run_time=0.1)

        # Spider pulse
        ring = Circle(radius=0.5, color=POS, stroke_width=3).move_to(center)
        self.play(ring.animate.scale(3).set_stroke(opacity=0), run_time=0.8)
        self.remove(ring)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  14. DYNAMIC ALLOCATION — Weight Rebalance Animation
# ═════════════════════════════════════════════════════════════════════════════

class Vis_DynamicAllocation(Scene):
    def construct(self):
        section_title("Dynamic Allocation", self)

        panel = math_panel([
            r"\Delta w_i = w_i^{\text{target}} - w_i^{\text{current}}",
            r"\text{Rebal if } |\Delta w_i| > \theta_{\text{drift}}",
            r"\theta_{\text{drift}} = 2\%",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([-0.8, 5.5, 1], [0, 0.55, 0.1], x_len=5.0, y_len=3.5)
        self.play(Create(axes), run_time=0.5)

        assets = ["Equities", "Bonds", "Gold", "Crypto", "Cash"]
        w_before = [0.40, 0.25, 0.10, 0.15, 0.10]
        w_after = [0.25, 0.40, 0.15, 0.08, 0.12]
        colors = [BLU, PUR, GOLD, NEG, POS]

        bars = VGroup()
        lbls = VGroup()
        for i, (name, w, col) in enumerate(zip(assets, w_before, colors)):
            h = axes.c2p(0, w)[1] - axes.c2p(0, 0)[1]
            bar = Rectangle(width=0.7, height=h, color=col, fill_opacity=0.8, stroke_width=1)
            bar.move_to(axes.c2p(i, w / 2))
            bars.add(bar)
            lbl = Text(name, font_size=10, color=WHT).next_to(axes.c2p(i, 0), DOWN, buff=0.1)
            lbls.add(lbl)

        self.play(
            LaggedStart(*[GrowFromEdge(b, DOWN) for b in bars], lag_ratio=0.1),
            FadeIn(lbls), run_time=1.0,
        )

        # Shock label
        shock = MathTex(r"\text{Rate Shock: } +200\,\text{bps}", font_size=18, color=NEG)
        shock.next_to(axes, UP, buff=0.2).align_to(axes, LEFT)
        self.play(Write(shock), run_time=0.5)
        self.wait(0.3)

        # Morph bars to new weights
        new_bars = VGroup()
        for i, (w, col) in enumerate(zip(w_after, colors)):
            h = axes.c2p(0, w)[1] - axes.c2p(0, 0)[1]
            bar = Rectangle(width=0.7, height=h, color=col, fill_opacity=0.8, stroke_width=1)
            bar.move_to(axes.c2p(i, w / 2))
            new_bars.add(bar)

        self.play(
            *[Transform(bars[i], new_bars[i]) for i in range(len(bars))],
            run_time=1.5, rate_func=rate_functions.ease_in_out_sine,
        )

        # Delta labels
        for i, (wb, wa, col) in enumerate(zip(w_before, w_after, colors)):
            delta = wa - wb
            sign = "+" if delta >= 0 else ""
            d_lbl = Text(f"{sign}{delta:.0%}", font_size=12, color=col)
            d_lbl.next_to(new_bars[i], UP, buff=0.08)
            self.play(FadeIn(d_lbl), run_time=0.15)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  15. STRESS TESTING — Shock Injection
# ═════════════════════════════════════════════════════════════════════════════

class Vis_StressTesting(Scene):
    def construct(self):
        section_title("Stress Testing: Tail Events", self)

        panel = math_panel([
            r"\text{Shock}:\; \Delta\text{NAV} = f(\text{VIX}, \rho \to 1)",
            r"\text{Protection} = \frac{\text{DD}_{\text{unhedged}} - \text{DD}_{\text{hedged}}}{\text{DD}_{\text{unhedged}}}",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        axes = left_axes([0, 10, 2], [30, 145, 20], x_len=5.5, y_len=3.8)
        self.play(Create(axes), run_time=0.6)

        t = np.linspace(0, 10, 200)

        # Unhedged: normal growth then massive crash
        y_un = np.where(t < 5, 100 + t * 4, (100 + 20) * 0.45 + (t - 5) * 1.5)
        un_line = axes.plot_line_graph(t, np.clip(y_un, 30, 145), add_vertex_dots=False, line_color=NEG)
        un_line.set_stroke(width=3)

        # Hedged: smaller drawdown, faster recovery
        y_hd = np.where(t < 5, 100 + t * 3.5, (100 + 17.5) * 0.82 + (t - 5) * 2.5)
        hd_line = axes.plot_line_graph(t, np.clip(y_hd, 30, 145), add_vertex_dots=False, line_color=POS)
        hd_line.set_stroke(width=4.5)
        hd_glow = hd_line.copy().set_stroke(width=14, opacity=0.15)

        self.play(Create(un_line), run_time=1.5)

        # Shock event marker
        shock_line = DashedLine(
            axes.c2p(5, 30), axes.c2p(5, 145), color=ACCENT, dash_length=0.12,
        ).set_stroke(width=2.5)
        shock_lbl = MathTex(r"\text{Macro Shock}", font_size=16, color=ACCENT)
        shock_lbl.next_to(axes.c2p(5, 140), RIGHT, buff=0.1)
        self.play(Create(shock_line), FadeIn(shock_lbl), run_time=0.6)

        self.play(Create(hd_glow), Create(hd_line), run_time=1.5)

        # Legend
        leg = VGroup(
            VGroup(Line(ORIGIN, RIGHT * 0.5, color=NEG, stroke_width=3), Text("Unhedged", font_size=12, color=NEG)).arrange(RIGHT, buff=0.1),
            VGroup(Line(ORIGIN, RIGHT * 0.5, color=POS, stroke_width=3), Text("BWC Hedged", font_size=12, color=POS)).arrange(RIGHT, buff=0.1),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1)
        leg.next_to(axes, DOWN, buff=0.35).align_to(axes, LEFT)
        self.play(FadeIn(leg), run_time=0.4)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  16. RATE LIMITER — Token Bucket Queue
# ═════════════════════════════════════════════════════════════════════════════

class Vis_RateLimiter(Scene):
    def construct(self):
        section_title("Rate Limiter: API Governance", self)

        panel = math_panel([
            r"\text{Tokens}(t) = \min\!\big(B,\; T_{t-1} + r \cdot \Delta t\big)",
            r"\text{FRED: } 120\;\text{req/min}",
            r"\text{Backoff: } t_{n+1} = 2^n \cdot t_0",
        ])
        self.play(FadeIn(panel, shift=LEFT * 0.3), run_time=0.8)

        anchor = np.array([-2.5, 0.0, 0])

        # Request stream (left)
        req_box = RoundedRectangle(
            width=1.5, height=2.2, corner_radius=0.08,
            color=BLU, fill_opacity=0.1, stroke_width=1.5,
        ).move_to(anchor + LEFT * 2)
        req_lbl = Text("Requests", font_size=13, color=BLU).move_to(req_box.get_center())
        self.play(FadeIn(req_box), FadeIn(req_lbl), run_time=0.4)

        # Token bucket (center)
        bucket = RoundedRectangle(
            width=1.2, height=2.5, corner_radius=0.1,
            color=ACCENT, fill_opacity=0.08, stroke_width=2,
        ).move_to(anchor)
        bucket_lbl = MathTex(r"Q(t)", font_size=18, color=ACCENT).next_to(bucket, UP, buff=0.15)
        self.play(Create(bucket), FadeIn(bucket_lbl), run_time=0.5)

        # API endpoint (right)
        api_box = RoundedRectangle(
            width=1.5, height=2.2, corner_radius=0.08,
            color=PUR, fill_opacity=0.1, stroke_width=1.5,
        ).move_to(anchor + RIGHT * 2)
        api_lbl = Text("API", font_size=13, color=PUR).move_to(api_box.get_center())
        self.play(FadeIn(api_box), FadeIn(api_lbl), run_time=0.4)

        # Arrows
        arr_in = Arrow(req_box.get_right(), bucket.get_left(), buff=0.08, color=MUTED, stroke_width=1.5)
        arr_out = Arrow(bucket.get_right(), api_box.get_left(), buff=0.08, color=POS, stroke_width=1.5)
        self.play(Create(arr_in), Create(arr_out), run_time=0.4)

        # Fill bucket with tokens
        tokens = VGroup()
        for i in range(8):
            tk = Circle(
                radius=0.08, color=ACCENT, fill_opacity=0.7, stroke_width=1,
            ).move_to(bucket.get_bottom() + UP * (0.2 + i * 0.28))
            tokens.add(tk)
        self.play(LaggedStart(*[FadeIn(tk, shift=UP * 0.1) for tk in tokens], lag_ratio=0.06), run_time=0.8)

        # Drain tokens (requests consuming them)
        for tk in tokens[:5]:
            self.play(
                tk.animate.move_to(api_box.get_center()).set_color(POS).scale(0.5),
                run_time=0.2, rate_func=smootherstep,
            )
            self.play(FadeOut(tk), run_time=0.05)

        # Refill
        new_tokens = VGroup()
        for i in range(3):
            tk = Circle(
                radius=0.08, color=GOLD, fill_opacity=0.7, stroke_width=1,
            ).move_to(bucket.get_top() + DOWN * 0.2)
            new_tokens.add(tk)
            self.play(
                tk.animate.move_to(bucket.get_bottom() + UP * (0.2 + (3 + i) * 0.28)),
                run_time=0.2,
            )

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  17. PROJECT ARCHITECTURE — Full System with Particles
# ═════════════════════════════════════════════════════════════════════════════

class Vis_ProjectArchitecture(Scene):
    def construct(self):
        section_title("BWC: Full Architecture", self)

        # Vertical pipeline
        modules = [
            ("Web Spiders", [-3.5, 3.0, 0], BLU),
            ("FRED / Macro", [-3.5, 1.6, 0], TEAL),
            ("Appwrite Cloud", [0, 3.0, 0], PUR),
            ("DuckDB Cache", [0, 1.6, 0], BLU),
            ("Feature Engine", [0, 0.0, 0], PUR),
            ("Macro Model", [3.5, 0.0, 0], GOLD),
            ("Fusion Agent", [0, -1.5, 0], ACCENT),
            ("Optimizer", [0, -2.8, 0], POS),
            ("Risk Manager", [3.5, -1.5, 0], NEG),
            ("Backtest", [-3.5, -1.5, 0], TEAL),
            ("Dashboard", [0, -4.0, 0], WHT),
        ]

        nodes = {}
        for name, pos, col in modules:
            bg = RoundedRectangle(
                width=2.0, height=0.5, corner_radius=0.08,
                color=col, fill_opacity=0.12, stroke_width=1.5,
            ).move_to(pos)
            lbl = Text(name, font_size=11, color=WHT, weight="BOLD").move_to(bg.get_center())
            grp = VGroup(bg, lbl)
            nodes[name] = grp

        self.play(
            LaggedStart(*[FadeIn(n, scale=0.9) for n in nodes.values()], lag_ratio=0.06),
            run_time=2.0,
        )

        connections = [
            ("Web Spiders", "Appwrite Cloud"),
            ("FRED / Macro", "DuckDB Cache"),
            ("Appwrite Cloud", "DuckDB Cache"),
            ("DuckDB Cache", "Feature Engine"),
            ("DuckDB Cache", "Macro Model"),
            ("Feature Engine", "Fusion Agent"),
            ("Macro Model", "Fusion Agent"),
            ("Fusion Agent", "Optimizer"),
            ("Optimizer", "Risk Manager"),
            ("Optimizer", "Dashboard"),
            ("Fusion Agent", "Backtest"),
            ("Backtest", "Dashboard"),
            ("Risk Manager", "Dashboard"),
        ]

        arrows = VGroup()
        for src, dst in connections:
            s, d = nodes[src], nodes[dst]
            a = Arrow(
                s.get_center(), d.get_center(),
                buff=0.35, color=MUTED, stroke_width=1.2, tip_length=0.1,
            )
            arrows.add(a)

        self.play(
            LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.04),
            run_time=1.5,
        )

        # Main data flow particle
        main_flow = [
            "Web Spiders", "Appwrite Cloud", "DuckDB Cache",
            "Feature Engine", "Fusion Agent", "Optimizer", "Dashboard",
        ]
        pkt = GlowDot(nodes[main_flow[0]].get_center(), color=POS, radius=0.09, glow=4)
        self.add(pkt)
        for i in range(len(main_flow) - 1):
            self.play(
                pkt.animate.move_to(nodes[main_flow[i + 1]].get_center()),
                run_time=0.3, rate_func=smootherstep,
            )
        self.play(FadeOut(pkt), run_time=0.15)

        # Macro side flow
        pkt2 = GlowDot(nodes["FRED / Macro"].get_center(), color=GOLD, radius=0.07, glow=3)
        self.add(pkt2)
        for nm in ["DuckDB Cache", "Macro Model", "Fusion Agent"]:
            self.play(pkt2.animate.move_to(nodes[nm].get_center()), run_time=0.25, rate_func=smootherstep)
        self.play(FadeOut(pkt2), run_time=0.1)

        self.wait(2)


# ═════════════════════════════════════════════════════════════════════════════
#  18. STOCHASTIC LOCAL VOL SURFACE — 3D Implied Volatility
# ═════════════════════════════════════════════════════════════════════════════

class Vis_StochasticVolSurface(ThreeDScene):
    def construct(self):
        title = Text("Stochastic Local Volatility Surface", font_size=28, color=WHT, weight="BOLD").to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)
        self.play(FadeIn(title), run_time=0.5)

        eq = MathTex(
            r"\sigma_{\text{LV}}(K/S,\;T)", font_size=26, color=ACCENT
        ).to_corner(UR).shift(DOWN * 0.8 + LEFT * 0.4)
        self.add_fixed_in_frame_mobjects(eq)
        self.play(Write(eq), run_time=0.6)

        self.set_camera_orientation(phi=65 * DEGREES, theta=-50 * DEGREES, zoom=0.7)

        axes = ThreeDAxes(
            x_range=[0.5, 1.5, 0.25],
            y_range=[0.1, 2.0, 0.5],
            z_range=[0, 0.6, 0.1],
            x_length=6, y_length=6, z_length=4,
            axis_config={"color": MUTED},
        )
        x_lbl = axes.get_x_axis_label(MathTex("K/S", font_size=20, color=WHT))
        y_lbl = axes.get_y_axis_label(MathTex("T", font_size=20, color=WHT))
        z_lbl = axes.get_z_axis_label(MathTex(r"\sigma", font_size=20, color=WHT))
        self.add(axes, x_lbl, y_lbl, z_lbl)

        def vol_surface(m, t):
            base = 0.20 + 0.05 * np.exp(-t)
            smile = 0.15 * (m - 1.0) ** 2
            skew = -0.08 * (m - 1.0) * np.exp(-0.5 * t)
            wings = 0.02 * np.exp(-2.0 * t) * (m - 1.0) ** 4
            return np.clip(base + smile + skew + wings, 0.05, 0.60)

        surface = Surface(
            lambda u, v: axes.c2p(u, v, vol_surface(u, v)),
            u_range=[0.5, 1.5], v_range=[0.1, 2.0],
            resolution=(36, 36),
            fill_opacity=0.7, stroke_width=0.4, stroke_color=MUTED,
        )
        surface.set_fill_by_value(
            axes=axes,
            colorscale=[
                (POS, 0.10), (BLU, 0.20), (PUR, 0.30),
                (ACCENT, 0.40), (NEG, 0.55),
            ],
            axis=2,
        )

        self.play(Create(surface), run_time=3)

        self.begin_ambient_camera_rotation(rate=0.12)
        self.wait(5)

        peak = Dot3D(axes.c2p(0.7, 0.2, vol_surface(0.7, 0.2)), color=NEG, radius=0.08)
        self.play(FadeIn(peak, scale=2.5), run_time=0.6)
        self.wait(3)
        self.stop_ambient_camera_rotation()
