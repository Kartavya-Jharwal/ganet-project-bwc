"""
Project BWC — Final Curated Manim Scenes (17 of 37).

Consolidated from:
  - docs/scenes.py        (20 scenes — mathematical concepts)
  - docs/project_scenes.py (12 scenes — project architecture)
  - docs/combined_scenes.py (5 scenes — philosophical/cinematic)

Selection balances pure math, project-specific architecture, and cinematic
philosophical visualizations. Every scene carries a LaymanInsight or
PhilosophyInsight panel for accessibility.
"""

import numpy as np
from manim import *

# ── Institutional Palette ────────────────────────────────────────────────────
COLOR_BG = "#050505"
COLOR_ACCENT = "#eb5e28"
COLOR_POSITIVE = "#00ff88"
COLOR_NEGATIVE = "#ff3366"
COLOR_MUTED = "#52525b"
COLOR_WHITE = "#f4f4f5"
COLOR_BLUE = "#3b82f6"
COLOR_PURPLE = "#8b5cf6"

config.background_color = COLOR_BG


# ── Shared Helpers ───────────────────────────────────────────────────────────

class GlowDot(VGroup):
    """A dot with a soft radial glow halo."""

    def __init__(self, point, color=COLOR_POSITIVE, radius=0.05, glow_factor=3, **kwargs):
        super().__init__(**kwargs)
        self.center_dot = Dot(point, radius=radius, color=color)
        self.glow = Dot(point, radius=radius * glow_factor, color=color, fill_opacity=0.2)
        self.add(self.glow, self.center_dot)


def LaymanInsight(title_str, body_str):
    """Blue-bordered insight panel anchored to the right edge."""
    box = RoundedRectangle(
        corner_radius=0.2, width=4.2, height=3.0, color=COLOR_BLUE, fill_opacity=0.1
    )
    title = Text(title_str, font_size=20, color=COLOR_ACCENT).move_to(box.get_top() + DOWN * 0.4)
    body = Text(body_str, font_size=16, line_spacing=1.3).next_to(title, DOWN, buff=0.3)
    body.set_color(COLOR_WHITE)
    return VGroup(box, title, body).to_edge(RIGHT, buff=0.5).set_z_index(10)


def PhilosophyInsight(title_str, body_str):
    """Muted-bordered philosophical insight panel anchored to the right edge."""
    box = RoundedRectangle(
        corner_radius=0.1, width=4.5, height=2.8, color=COLOR_MUTED, fill_opacity=0.05
    )
    title = Text(title_str, font_size=22, color=COLOR_WHITE).move_to(box.get_top() + DOWN * 0.5)
    body = Text(body_str, font_size=16, line_spacing=1.4).next_to(title, DOWN, buff=0.4)
    body.set_color(COLOR_MUTED)
    return VGroup(box, title, body).to_edge(RIGHT, buff=0.5).set_z_index(10)


def build_glow(obj):
    """Return a wide, semi-transparent stroke copy of *obj* for a glow effect."""
    return obj.copy().set_color(COLOR_ACCENT).set_stroke(width=10, opacity=0.3)


def _mini_line_graph(x, y, line_color=COLOR_WHITE):
    """Lightweight VMobject line graph for embedding inside dashboard panels."""
    pts = [np.array([xx, yy, 0]) for xx, yy in zip(x, y, strict=False)]
    return VMobject().set_points_as_corners(pts).set_color(line_color)


# ═════════════════════════════════════════════════════════════════════════════
#  PURE MATH SCENES (1–11)
# ═════════════════════════════════════════════════════════════════════════════


class Scene01_GeometricBrownianMotion(MovingCameraScene):
    """Geometric Brownian Motion — Monte Carlo SDE paths with terminal distribution.

    Bug-fix applied: uses Create() instead of MoveAlongPath() on LineGraph objects.
    """

    def construct(self):
        title = Text("1. Stochastic Differential Equations", font_size=32).to_corner(UL)
        self.add(title)

        sde = (
            MathTex("dS_t", "=", "\\mu", "S_t", "dt", "+", "\\sigma", "S_t", "dW_t")
            .to_edge(LEFT, buff=1)
            .shift(UP * 1)
        )
        self.play(Write(sde), run_time=1.5)

        insight = LaymanInsight(
            "Investor Insight",
            "Instead of guessing one\naverage future, we deploy\nthousands of parallel\nuniverses. This mathematically\nreveals our worst-case drop.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[0, 100, 20],
                y_range=[0, 200, 50],
                x_length=5,
                y_length=4,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 1)
        )
        x_label = axes.get_x_axis_label(Text("t", font_size=18, color=COLOR_WHITE), edge=DOWN, direction=DOWN)
        y_label = axes.get_y_axis_label(MathTex("S_t", font_size=22, color=COLOR_WHITE), edge=LEFT, direction=LEFT)
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        lines = VGroup()
        np.random.seed(42)
        for _ in range(12):
            path = [100.0]
            for _ in range(80):
                path.append(
                    path[-1]
                    * np.exp((0.001 - 0.5 * 0.005) + np.sqrt(0.005) * np.random.normal())
                )
            c = axes.plot_line_graph(
                x_values=np.arange(81),
                y_values=path,
                line_color=COLOR_BLUE,
                add_vertex_dots=False,
            ).set_stroke(opacity=0.4)
            self.play(Create(c), run_time=0.6, rate_func=linear)
            lines.add(c)

        bell = axes.plot(
            lambda x: 100 + 40 * np.exp(-0.5 * ((x - 100) / 20) ** 2), color=COLOR_ACCENT
        )
        self.play(Create(bell), rate_func=rate_functions.ease_in_out_sine)
        self.wait(1)


class Scene02_MarkowitzEfficientFrontier(MovingCameraScene):
    """Markowitz efficient frontier — random portfolios with the optimal boundary."""

    def construct(self):
        title = Text("2. Modern Portfolio Theory", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "You don't want to just pick\nstocks randomly. You want to\nfind the absolute boundary\n(the optimal edge) where\nrisk is minimized for every\ndrop of return.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[0, 0.4, 0.1],
                y_range=[0, 0.25, 0.05],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            MathTex(r"\sigma", font_size=22, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            MathTex(r"\mathbb{E}[r]", font_size=22, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        dots = VGroup()
        np.random.seed(99)
        for _ in range(250):
            vol = np.random.uniform(0.05, 0.35)
            max_r = 0.15 * np.sqrt((vol - 0.05) / 0.2) if vol > 0.05 else 0
            if max_r > 0:
                dots.add(
                    Dot(axes.c2p(vol, np.random.uniform(0.01, max_r)), color=COLOR_MUTED, radius=0.03)
                )

        self.play(LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.01), run_time=2)

        frontier = axes.plot(
            lambda x: 0.15 * np.sqrt((x - 0.05) / 0.2), x_range=[0.05, 0.35], color=COLOR_POSITIVE
        )
        glow = axes.plot(
            lambda x: 0.15 * np.sqrt((x - 0.05) / 0.2), x_range=[0.05, 0.35], color=COLOR_POSITIVE
        ).set_stroke(width=10, opacity=0.3)
        self.play(Create(frontier), FadeIn(glow), run_time=2)

        optimal = GlowDot(
            axes.c2p(0.15, 0.15 * np.sqrt(0.5)), color=COLOR_ACCENT, radius=0.05, glow_factor=5
        )
        self.play(FadeIn(optimal, scale=2))
        self.wait(1)


class Scene03_CapitalMarketLine(Scene):
    """Capital Market Line — tangent from risk-free rate to the efficient frontier."""

    def construct(self):
        title = Text("3. Capital Market Line & Tangency", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "By holding some cash alongside\nthe optimal portfolio, we can\nslide up and down a perfectly\nstraight line, escaping the\nlimitations of stocks alone.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[0, 0.3, 0.1],
                y_range=[0, 0.2, 0.05],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            MathTex(r"\sigma", font_size=22, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            MathTex(r"\mathbb{E}[r]", font_size=22, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        rf_dot = Dot(axes.c2p(0, 0.02), color=COLOR_WHITE)
        frontier = axes.plot(
            lambda x: 0.15 * np.sqrt((x - 0.05) / 0.2), x_range=[0.05, 0.3], color=COLOR_POSITIVE
        )

        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label), Create(frontier), FadeIn(rf_dot))

        tracker = ValueTracker(0.3)

        def get_cml():
            x = tracker.get_value()
            y = 0.15 * np.sqrt((x - 0.05) / 0.2)
            return Line(
                rf_dot.get_center(),
                axes.c2p(x + 0.1, y + (y - 0.02) / x * 0.1),
                color=COLOR_ACCENT,
            ).set_z_index(3)

        self.add(always_redraw(get_cml))
        self.play(
            tracker.animate.set_value(0.1), run_time=3, rate_func=rate_functions.ease_in_out_sine
        )
        self.wait()


class Scene04_AlphaBetaOrthogonality(Scene):
    """Alpha/Beta factor decomposition via vector projection."""

    def construct(self):
        title = Text("4. Alpha & Beta Factor Orthogonality", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Beta is just riding the\ngeneral market wave. Alpha\nis the true, orthogonal skill\nof the manager to generate\nexcess returns out of thin air.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        plane = NumberPlane(
            x_range=[-1, 5],
            y_range=[-1, 5],
            background_line_style={"stroke_opacity": 0.2},
            x_length=6,
            y_length=6,
        ).to_edge(LEFT, buff=1)
        self.play(FadeIn(plane))

        vm = Arrow(plane.c2p(0, 0), plane.c2p(4, 2), color=COLOR_BLUE, buff=0)
        vp = Arrow(plane.c2p(0, 0), plane.c2p(3, 4), color=COLOR_POSITIVE, buff=0)
        self.play(Create(vm), Create(vp))

        proj = plane.c2p(*(np.dot([3, 4], [4, 2]) / np.dot([4, 2], [4, 2]) * np.array([4, 2])))
        v_beta = Arrow(plane.c2p(0, 0), proj, color=COLOR_ACCENT, buff=0)
        v_alpha = Arrow(proj, plane.c2p(3, 4), color=COLOR_PURPLE, buff=0)

        beta_lbl = MathTex(r"\beta", font_size=28, color=COLOR_ACCENT).next_to(v_beta, DOWN, buff=0.15)
        alpha_lbl = MathTex(r"\alpha", font_size=28, color=COLOR_PURPLE).next_to(v_alpha, RIGHT, buff=0.15)

        self.play(Create(v_beta), FadeIn(beta_lbl))
        self.play(Create(v_alpha), FadeIn(alpha_lbl))
        self.wait(1)


class Scene05_ConditionalValueAtRisk(Scene):
    """CVaR — tail risk beyond the VaR threshold on a Gaussian return distribution."""

    def construct(self):
        title = Text("5. Conditional Value at Risk (CVaR)", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Standard 'VaR' tells you where\nthe cliff edge is. 'CVaR'\nactually measures the average\ndepth of the fall once you go\nover the cliff.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[-4, 4, 1],
                y_range=[0, 0.5, 0.1],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            Text("Return (σ)", font_size=16, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            Text("Density", font_size=16, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        curve = axes.plot(
            lambda x: 1 / (np.sqrt(2 * np.pi)) * np.exp(-0.5 * x ** 2), color=COLOR_WHITE
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label), Create(curve))

        rects = axes.get_riemann_rectangles(
            curve, x_range=[-4, -1.645], dx=0.4, color=COLOR_ACCENT, fill_opacity=0.6
        )
        self.play(Create(rects), run_time=2)

        smooth_area = axes.get_area(curve, x_range=[-4, -1.645], color=COLOR_NEGATIVE, opacity=0.8)
        self.play(Transform(rects, smooth_area), run_time=2)

        line = axes.get_vertical_line(
            axes.c2p(-1.645, 1 / (np.sqrt(2 * np.pi)) * np.exp(-0.5 * (-1.645) ** 2)),
            color=COLOR_NEGATIVE,
        )
        var_lbl = Text("VaR 95%", font_size=14, color=COLOR_NEGATIVE).next_to(line, UP, buff=0.1)
        self.play(Create(line), FadeIn(var_lbl))
        self.wait(1)


class Scene06_KellyCriterionParabola(Scene):
    """Kelly Criterion — optimal bet sizing as a concave parabola with tangent sweep."""

    def construct(self):
        title = Text("6. The Kelly Parabola", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "If you bet cautiously, you\ngrow slowly. But if you\nbet past the optimal peak,\nvolatility destroys you and\nyou mathematically go broke.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[0, 1, 0.2],
                y_range=[0, 0.1, 0.02],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            Text("Fraction bet", font_size=16, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            Text("E[log growth]", font_size=16, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        curve = axes.plot(
            lambda x: 0.15 * x - 0.5 * 0.2 * x ** 2, x_range=[0, 1], color=COLOR_POSITIVE
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label), Create(curve))

        tracker = ValueTracker(0.1)
        tangent = always_redraw(
            lambda: axes.plot(
                lambda x: (
                    (0.15 - 0.2 * tracker.get_value()) * (x - tracker.get_value())
                    + (0.15 * tracker.get_value() - 0.5 * 0.2 * tracker.get_value() ** 2)
                ),
                color=COLOR_ACCENT,
                x_range=[tracker.get_value() - 0.2, tracker.get_value() + 0.2],
            )
        )

        peak_dot = always_redraw(
            lambda: GlowDot(
                axes.c2p(
                    tracker.get_value(),
                    0.15 * tracker.get_value() - 0.5 * 0.2 * tracker.get_value() ** 2,
                ),
                color=COLOR_ACCENT,
                radius=0.04,
            )
        )

        self.add(tangent, peak_dot)
        self.play(
            tracker.animate.set_value(0.75), run_time=3, rate_func=rate_functions.ease_in_out_sine
        )
        self.wait(1)


class Scene07_CovarianceGeometry(ThreeDScene):
    """3D covariance manifold — warped surface showing correlation structure."""

    def construct(self):
        title = Text("7. Covariance Space (3D Manifold)", font_size=32).to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Assets never move in a vacuum.\nTheir overlapping risks warp\nand stretch the entire portfolio\nspace, meaning unseen dangers\nlurk in their correlations.",
        )
        insight.to_corner(DR).shift(UP * 0.5 + LEFT * 0.5)
        self.add_fixed_in_frame_mobjects(insight)
        self.play(FadeIn(insight))

        self.set_camera_orientation(phi=65 * DEGREES, theta=-45 * DEGREES)
        axes = ThreeDAxes(
            axis_config={"color": COLOR_MUTED},
        )
        x_lbl = axes.get_x_axis_label(MathTex("x_1", font_size=22, color=COLOR_WHITE))
        y_lbl = axes.get_y_axis_label(MathTex("x_2", font_size=22, color=COLOR_WHITE))
        z_lbl = axes.get_z_axis_label(MathTex(r"\text{Cov}", font_size=22, color=COLOR_WHITE))
        self.add(axes, x_lbl, y_lbl, z_lbl)

        surface = Surface(
            lambda u, v: axes.c2p(u, v, np.sin(u) * np.cos(v)),
            u_range=[-PI, PI],
            v_range=[-PI, PI],
            resolution=(20, 20),
            fill_opacity=0.6,
            stroke_width=1,
            stroke_color=COLOR_BLUE,
        )
        surface.set_fill_by_checkerboard(COLOR_PURPLE, COLOR_BLUE)
        self.play(Create(surface), run_time=2)

        self.begin_ambient_camera_rotation(rate=0.2)
        self.play(
            surface.animate.apply_matrix([[1.5, 0.8, 0], [0.8, 1.2, 0], [0, 0, 1]]),
            run_time=4,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.wait(2)
        self.stop_ambient_camera_rotation()


class Scene08_YieldCurveDynamics(Scene):
    """Dynamic yield curve inversion — normal to inverted via Nelson-Siegel-like model."""

    def construct(self):
        title = Text("8. Dynamic Yield Curve", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Normally, locking money up\nlonger pays more. When this\ncurve inverts, the institutional\nbond market is flashing a\nmassive recession warning.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[0, 30, 5],
                y_range=[0, 6, 1],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            Text("Maturity (yr)", font_size=16, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            Text("Yield %", font_size=16, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        t = ValueTracker(0)
        curve = always_redraw(
            lambda: axes.plot(
                lambda x: (
                    interpolate(1.0, 5.0, t.get_value())
                    + (interpolate(5.0, 4.0, t.get_value()) - interpolate(1.0, 5.0, t.get_value()))
                    * (1 - np.exp(-0.2 * x))
                ),
                color=interpolate_color(COLOR_BLUE, COLOR_NEGATIVE, t.get_value()),
            )
        )
        state_lbl = always_redraw(
            lambda: Text(
                "NORMAL" if t.get_value() < 0.5 else "INVERTED",
                font_size=20,
                color=COLOR_POSITIVE if t.get_value() < 0.5 else COLOR_NEGATIVE,
            ).next_to(axes, UP, buff=0.15).align_to(axes, LEFT)
        )
        self.add(curve, state_lbl)
        self.play(t.animate.set_value(1), run_time=3, rate_func=rate_functions.ease_in_out_sine)
        self.wait(1)


class Scene09_JumpDiffusionPoisson(Scene):
    """Merton jump-diffusion — Brownian motion with Poisson crash shocks."""

    def construct(self):
        title = Text("9. Brownian Motion w/ Poisson Shocks", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Real markets don't move in\nsmooth continuous lines. They\nsuffer massive, unpredictable\nlightning crashes (jumps) that\nbreak standard risk models.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[0, 10, 1],
                y_range=[0, 20, 5],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            Text("t", font_size=18, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            MathTex("S_t", font_size=22, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        np.random.seed(11)
        y = [10.0]
        for _ in range(1, 100):
            jump = -3.0 if np.random.rand() < 0.03 else 0.0
            y.append(y[-1] + 0.01 + np.random.normal(0, 0.2) + jump)

        g = axes.plot_line_graph(
            np.linspace(0, 10, 100), y, add_vertex_dots=False, line_color=COLOR_NEGATIVE
        )
        self.play(Create(g, run_time=3, rate_func=linear))

        jump_eq = MathTex(
            r"dS = \mu\,dt + \sigma\,dW + J\,dN_t",
            font_size=24,
            color=COLOR_ACCENT,
        ).next_to(axes, UP, buff=0.15).align_to(axes, LEFT)
        self.play(Write(jump_eq))
        self.wait(1)


class Scene10_QuadraticVariationBrownianMotion(Scene):
    """Quadratic Variation of Brownian Motion — Monte Carlo convergence to <B>_t = t."""

    def construct(self):
        title = Text("10. Quadratic Variation of Brownian Motion", font_size=30).to_corner(UL)
        self.add(title)

        eq_box = RoundedRectangle(
            corner_radius=0.2, width=4.5, height=4.5, color=COLOR_BLUE, fill_opacity=0.08
        ).to_edge(RIGHT, buff=0.4).shift(UP * 0.3)

        eq_title = Text("Quadratic Variation", font_size=18, color=COLOR_ACCENT).move_to(
            eq_box.get_top() + DOWN * 0.45
        )
        eq_def = MathTex(
            r"\langle B \rangle_t = t", font_size=36, color=COLOR_WHITE
        ).next_to(eq_title, DOWN, buff=0.3)

        eq_sum = MathTex(
            r"\sum_{i} \left( B_{t_{i+1}} - B_{t_i} \right)^2 \to t",
            font_size=26,
            color=COLOR_MUTED,
        ).next_to(eq_def, DOWN, buff=0.25)

        eq_note = Text(
            "As partition size → 0,\nthe sum of squared\nincrements converges\nto elapsed time t.",
            font_size=14,
            line_spacing=1.3,
            color=COLOR_WHITE,
        ).next_to(eq_sum, DOWN, buff=0.3)

        self.play(FadeIn(eq_box), Write(eq_title))
        self.play(Write(eq_def), run_time=1.5)
        self.play(FadeIn(eq_sum), FadeIn(eq_note))

        axes = Axes(
            x_range=[0, 1.0, 0.2],
            y_range=[0, 2.0, 0.5],
            x_length=6.5,
            y_length=4.5,
            axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 20},
        ).to_edge(LEFT, buff=0.8).shift(DOWN * 0.3)

        x_label = axes.get_x_axis_label(
            Text("t", font_size=20, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            MathTex(r"\langle B \rangle_t", font_size=24, color=COLOR_WHITE),
            edge=LEFT,
            direction=LEFT,
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        true_line = axes.plot(lambda t: t, x_range=[0, 1.0], color=COLOR_ACCENT, stroke_width=3)
        true_label = Text("⟨B⟩ₜ = t (theory)", font_size=14, color=COLOR_ACCENT).next_to(
            true_line, UP, buff=0.15
        )
        self.play(Create(true_line), FadeIn(true_label), run_time=1.5)

        partition_configs = [
            (10, "#ff3366", "n=10"),
            (50, "#ffaa33", "n=50"),
            (200, "#33ccff", "n=200"),
            (1000, "#00ff88", "n=1000"),
        ]

        np.random.seed(42)
        legend_items = VGroup()

        for n_partitions, color, label in partition_configs:
            dt_step = 1.0 / n_partitions
            n_mc = 50
            qv_curves = []
            for _ in range(n_mc):
                increments = np.random.normal(0, np.sqrt(dt_step), n_partitions)
                sq_increments = increments ** 2
                cumulative_qv = np.cumsum(sq_increments)
                qv_curves.append(cumulative_qv)

            avg_qv = np.mean(qv_curves, axis=0)
            t_vals = np.linspace(dt_step, 1.0, n_partitions)

            step = max(1, n_partitions // 100)
            t_plot = t_vals[::step]
            qv_plot = avg_qv[::step]

            graph = axes.plot_line_graph(
                x_values=t_plot,
                y_values=qv_plot,
                add_vertex_dots=False,
                line_color=color,
            ).set_stroke(width=2, opacity=0.8)

            leg_dot = Dot(color=color, radius=0.06)
            leg_text = Text(label, font_size=14, color=color)
            leg_entry = VGroup(leg_dot, leg_text).arrange(RIGHT, buff=0.15)
            legend_items.add(leg_entry)

            self.play(Create(graph), run_time=0.8)

        legend_items.arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        legend_items.next_to(axes, DOWN, buff=0.3).align_to(axes, LEFT)
        self.play(FadeIn(legend_items))

        converge_text = Text(
            "Finer partitions → convergence to t",
            font_size=16,
            color=COLOR_POSITIVE,
        ).next_to(axes, DOWN, buff=0.05)
        self.play(FadeIn(converge_text, shift=UP * 0.2))
        self.wait(3)


class Scene11_StochasticLocalVolatilitySurface(ThreeDScene):
    """Stochastic Local Volatility surface — 3D implied vol σ(K/S, T)."""

    def construct(self):
        title = Text("11. Stochastic Local Volatility Surface", font_size=30).to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)

        insight = LaymanInsight(
            "Options Insight",
            "This 3D 'chopping board'\nis the implied volatility\nsurface σ(K, T). Peaks show\nunstable pricing regions.\nUsed for delta hedging\ncalibration.",
        )
        insight.to_corner(DR).shift(UP * 0.3 + LEFT * 0.3)
        self.add_fixed_in_frame_mobjects(insight)
        self.play(FadeIn(insight))

        eq = MathTex(
            r"\sigma_{LV}(S, t, K, T)", font_size=30, color=COLOR_ACCENT
        ).to_corner(UR).shift(DOWN * 1.5 + LEFT * 0.5)
        self.add_fixed_in_frame_mobjects(eq)
        self.play(Write(eq))

        self.set_camera_orientation(phi=65 * DEGREES, theta=-50 * DEGREES, zoom=0.7)

        axes = ThreeDAxes(
            x_range=[0.5, 1.5, 0.25],
            y_range=[0.1, 2.0, 0.5],
            z_range=[0, 0.6, 0.1],
            x_length=6,
            y_length=6,
            z_length=4,
            axis_config={"color": COLOR_MUTED},
        )
        x_lbl = axes.get_x_axis_label(
            MathTex("K/S", font_size=24, color=COLOR_WHITE), edge=RIGHT, direction=RIGHT
        )
        y_lbl = axes.get_y_axis_label(
            MathTex("T", font_size=24, color=COLOR_WHITE), edge=UP, direction=UP
        )
        z_lbl = axes.get_z_axis_label(
            MathTex(r"\sigma", font_size=24, color=COLOR_WHITE), edge=OUT, direction=OUT
        )
        self.add(axes, x_lbl, y_lbl, z_lbl)

        def vol_surface(moneyness, maturity):
            base_vol = 0.20 + 0.05 * np.exp(-maturity)
            smile = 0.15 * (moneyness - 1.0) ** 2
            skew = -0.08 * (moneyness - 1.0) * np.exp(-0.5 * maturity)
            wings = 0.02 * np.exp(-2.0 * maturity) * (moneyness - 1.0) ** 4
            rough = 0.01 * np.sin(8 * moneyness) * np.cos(3 * maturity)
            return np.clip(base_vol + smile + skew + wings + rough, 0.05, 0.60)

        surface = Surface(
            lambda u, v: axes.c2p(u, v, vol_surface(u, v)),
            u_range=[0.5, 1.5],
            v_range=[0.1, 2.0],
            resolution=(40, 40),
            fill_opacity=0.7,
            stroke_width=0.5,
            stroke_color=COLOR_MUTED,
        )

        surface.set_fill_by_value(
            axes=axes,
            colorscale=[
                (COLOR_POSITIVE, 0.10),
                (COLOR_BLUE, 0.20),
                (COLOR_PURPLE, 0.30),
                (COLOR_ACCENT, 0.40),
                (COLOR_NEGATIVE, 0.55),
            ],
            axis=2,
        )

        self.play(Create(surface), run_time=3)

        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(4)

        peak_dot = Dot3D(
            axes.c2p(0.7, 0.2, vol_surface(0.7, 0.2)),
            color=COLOR_NEGATIVE,
            radius=0.08,
        )
        self.play(FadeIn(peak_dot, scale=2))
        self.wait(3)
        self.stop_ambient_camera_rotation()


# ═════════════════════════════════════════════════════════════════════════════
#  PROJECT-SPECIFIC SCENES (12–15)
# ═════════════════════════════════════════════════════════════════════════════


class Scene12_BWCArchitecture(Scene):
    """BWC core architecture — module dependency graph with data-flow particle."""

    def construct(self):
        title = Text("12. quant_monitor: Core Architecture", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "BWC Codebase",
            "Project BWC is divided into\nspecialized Python modules.\nData flows from Spiders to the\nDatabase, gets parsed into Features,\noptimized by Agents, and Backtested.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        modules = [
            ("quant_monitor/spiders", [-4, 2, 0]),
            ("quant_monitor/data", [-1.5, 2, 0]),
            ("quant_monitor/features", [-1.5, 0, 0]),
            ("quant_monitor/agent", [1.5, 0, 0]),
            ("quant_monitor/backtest", [1.5, -2, 0]),
            ("quant_monitor/dashboard", [4, -2, 0]),
        ]

        blocks = {}
        for name, pos in modules:
            bg = RoundedRectangle(width=2.5, height=0.8, color=COLOR_BLUE, fill_opacity=0.2)
            lbl = Text(name.split("/")[1].upper(), font_size=16, color=COLOR_WHITE)
            grp = VGroup(bg, lbl).move_to(pos)
            blocks[name] = grp

        arrows = []

        def _show_block_and_arrow(src_key, dst_key):
            self.play(FadeIn(blocks[dst_key]))
            a = Arrow(
                blocks[src_key].get_right() if blocks[src_key].get_center()[0] < blocks[dst_key].get_center()[0]
                else blocks[src_key].get_bottom(),
                blocks[dst_key].get_left() if blocks[src_key].get_center()[0] < blocks[dst_key].get_center()[0]
                else blocks[dst_key].get_top(),
                color=COLOR_ACCENT,
            )
            self.play(GrowArrow(a))
            arrows.append(a)

        self.play(FadeIn(blocks["quant_monitor/spiders"]))
        _show_block_and_arrow("quant_monitor/spiders", "quant_monitor/data")
        _show_block_and_arrow("quant_monitor/data", "quant_monitor/features")
        _show_block_and_arrow("quant_monitor/features", "quant_monitor/agent")
        _show_block_and_arrow("quant_monitor/agent", "quant_monitor/backtest")
        _show_block_and_arrow("quant_monitor/backtest", "quant_monitor/dashboard")

        particle = GlowDot(blocks["quant_monitor/spiders"].get_center(), color=COLOR_POSITIVE, radius=0.08)
        self.add(particle)
        flow_keys = [
            "quant_monitor/spiders", "quant_monitor/data", "quant_monitor/features",
            "quant_monitor/agent", "quant_monitor/backtest", "quant_monitor/dashboard",
        ]
        for i in range(len(flow_keys) - 1):
            self.play(
                MoveAlongPath(
                    particle,
                    Line(blocks[flow_keys[i]].get_center(), blocks[flow_keys[i + 1]].get_center()),
                ),
                run_time=0.5,
            )
        self.play(FadeOut(particle))
        self.wait(2)


class Scene13_FeatureEngineering(Scene):
    """Feature engineering — raw price to Bollinger bands via moving averages & volatility."""

    def construct(self):
        title = Text("13. quant_monitor.features", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Feature Engine",
            "Raw prices go into features/moving_averages\nand features/volatility. The engine\ntransforms chaos into mathematical\nsignals (like Bollinger bands)\nfor the AI to trade.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[0, 10, 1],
                y_range=[0, 10, 2],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            Text("t", font_size=18, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            Text("Price", font_size=16, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        np.random.seed(42)
        x_vals = np.linspace(0, 10, 100)
        raw = 5 + x_vals * 0.2 + np.random.normal(0, 1, 100)
        graph_raw = axes.plot_line_graph(x_vals, raw, add_vertex_dots=False, line_color=COLOR_MUTED)
        self.play(Create(graph_raw), run_time=1.5)

        ma_txt = (
            Text("moving_averages.py", font_size=16, color=COLOR_BLUE)
            .to_corner(UR)
            .shift(DOWN * 1.5 + LEFT * 4)
        )
        vol_txt = Text("volatility.py", font_size=16, color=COLOR_PURPLE).next_to(ma_txt, DOWN)
        self.play(Write(ma_txt), Write(vol_txt))

        smooth = 5 + x_vals * 0.2
        graph_smooth = axes.plot_line_graph(
            x_vals, smooth, add_vertex_dots=False, line_color=COLOR_BLUE
        ).set_stroke(width=4)
        band_up = axes.plot_line_graph(
            x_vals, smooth + 1.5, add_vertex_dots=False, line_color=COLOR_PURPLE
        )
        band_down = axes.plot_line_graph(
            x_vals, smooth - 1.5, add_vertex_dots=False, line_color=COLOR_PURPLE
        )

        self.play(Create(graph_smooth))
        self.play(Create(band_up), Create(band_down))

        area = axes.get_area(
            axes.plot(lambda x: 5 + x * 0.2 + 1.5),
            bounded_graph=axes.plot(lambda x: 5 + x * 0.2 - 1.5),
            color=COLOR_PURPLE,
            opacity=0.2,
        )
        self.play(FadeIn(area))
        self.wait(1)


class Scene14_BacktestEngine(Scene):
    """Backtest engine — BWC strategy equity curve vs S&P 500 benchmark."""

    def construct(self):
        title = Text("14. quant_monitor.backtest.engine", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Simulation Engine",
            "topological_run.py executes\nyears of historical market data\nin seconds. It stress-tests the\nportfolio logic across simulated\nmarket crashes.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[2018, 2024, 1],
                y_range=[0, 300, 100],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            Text("Year", font_size=16, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            Text("NAV", font_size=16, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        x_vals = np.linspace(2018, 2024, 100)
        sp500 = 100 * np.exp(0.08 * (x_vals - 2018))
        bwc = 100 * np.exp(0.15 * (x_vals - 2018))

        g_sp = axes.plot_line_graph(x_vals, sp500, add_vertex_dots=False, line_color=COLOR_MUTED)
        g_bwc = axes.plot_line_graph(
            x_vals, bwc, add_vertex_dots=False, line_color=COLOR_POSITIVE
        ).set_stroke(width=5)

        lbl_sp = Text("Benchmark", font_size=16, color=COLOR_MUTED).next_to(g_sp, RIGHT, buff=0.1)
        lbl_bwc = Text("BWC Algo Yield", font_size=16, color=COLOR_POSITIVE).next_to(
            g_bwc, RIGHT, buff=0.1
        )

        self.play(Create(g_sp), FadeIn(lbl_sp), run_time=2)
        self.play(
            Create(g_bwc), FadeIn(lbl_bwc), run_time=3, rate_func=rate_functions.ease_in_out_sine
        )
        self.wait(1)


class Scene15_StressTesting(Scene):
    """Stress testing — macro shock event with hedged vs unhedged equity curves."""

    def construct(self):
        title = Text("15. quant_monitor.backtest.stress", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Stress Testing",
            "We don't just optimize for\nthe sunny days. 'stress.py'\ninjects simulated macro shocks\n(like COVID-19 or 2008) to see\nif our portfolio survives.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(
                x_range=[0, 10, 2],
                y_range=[50, 150, 20],
                x_length=6,
                y_length=4.5,
                axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        x_label = axes.get_x_axis_label(
            Text("t (months)", font_size=16, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            Text("NAV", font_size=16, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        x_vals = np.linspace(0, 10, 100)

        y_shock = np.where(
            x_vals < 5,
            100 + x_vals * 3,
            (100 + 5 * 3) * 0.6 + (x_vals - 5) * 1,
        )

        y_bwc = np.where(
            x_vals < 5,
            100 + x_vals * 2.5,
            (100 + 5 * 2.5) * 0.9 + (x_vals - 5) * 2,
        )

        g_shock = axes.plot_line_graph(
            x_vals, y_shock, add_vertex_dots=False, line_color=COLOR_NEGATIVE
        )
        g_bwc = axes.plot_line_graph(
            x_vals, y_bwc, add_vertex_dots=False, line_color=COLOR_POSITIVE
        ).set_stroke(width=4)

        shock_line = axes.get_vertical_line(
            axes.c2p(5, 150), color=COLOR_WHITE, line_func=DashedLine
        )
        shock_text = Text("Macro Shock Event", font_size=16, color=COLOR_WHITE).next_to(
            shock_line, UP
        )

        self.play(Create(g_shock), run_time=2)
        self.play(Create(shock_line), Write(shock_text))
        self.play(Create(g_bwc), run_time=2)

        lbl_unhedged = Text("Unhedged", font_size=16, color=COLOR_NEGATIVE).next_to(
            g_shock.get_corner(UR), LEFT
        )
        lbl_bwc = Text("BWC Hedged", font_size=16, color=COLOR_POSITIVE).next_to(
            g_bwc.get_corner(UR), LEFT
        )
        self.play(FadeIn(lbl_unhedged), FadeIn(lbl_bwc))
        self.wait(1)


# ═════════════════════════════════════════════════════════════════════════════
#  PHILOSOPHICAL / CINEMATIC SCENES (16–17)
# ═════════════════════════════════════════════════════════════════════════════


class Scene16_RegimePhaseShift(Scene):
    """Regime phase shift — normal market state shatters into crisis with BWC alpha recovery."""

    def construct(self):
        title = Text("16. Phase Shifts & Stress", font_size=32).to_corner(UL)
        self.add(title)
        self.camera.background_color = COLOR_BG

        insight = PhilosophyInsight(
            "Regime Collapse",
            "The market is not a line, it's a state.\nWhen a crisis hits (x=5), the literal\nphysics of the environment shatter.\nCorrelations go to 1, math goes red.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.5))

        axes = Axes(
            x_range=[0, 10, 2],
            y_range=[0, 200, 50],
            x_length=6,
            y_length=4.5,
            axis_config={"color": COLOR_MUTED, "include_numbers": True, "font_size": 18},
        ).to_edge(LEFT, buff=1)
        x_label = axes.get_x_axis_label(
            Text("t", font_size=18, color=COLOR_WHITE), edge=DOWN, direction=DOWN
        )
        y_label = axes.get_y_axis_label(
            Text("NAV", font_size=16, color=COLOR_WHITE), edge=LEFT, direction=LEFT
        )
        self.play(Create(axes), FadeIn(x_label), FadeIn(y_label))

        x_vals_1 = np.linspace(0, 5, 100)
        y_vals_1 = 100 + x_vals_1 * 5 + np.sin(x_vals_1 * 4) * 10
        normal_graph = axes.plot_line_graph(
            x_vals_1, y_vals_1, add_vertex_dots=False, line_color=COLOR_BLUE
        )

        self.play(Create(normal_graph), run_time=2, rate_func=linear)

        shock_line = axes.get_vertical_line(axes.c2p(5, 200), color=COLOR_NEGATIVE).set_stroke(
            width=4
        )
        lbl = (
            Text("Regime Break", font_size=18, color=COLOR_NEGATIVE)
            .next_to(shock_line, RIGHT, buff=0.1)
            .shift(UP * 1.5)
        )

        self.play(
            Create(shock_line),
            FadeIn(lbl, shift=LEFT * 0.2),
            axes.animate.set_color(COLOR_MUTED),
            run_time=0.8,
            rate_func=rate_functions.ease_out_bounce,
        )

        x_vals_2 = np.linspace(5, 10, 100)
        np.random.seed(1)
        y_vals_2 = y_vals_1[-1] - (x_vals_2 - 5) * 20 + np.random.normal(0, 15, 100)
        crash_graph = axes.plot_line_graph(
            x_vals_2, y_vals_2, add_vertex_dots=False, line_color=COLOR_NEGATIVE
        ).set_stroke(width=2)

        self.play(Create(crash_graph), run_time=1.5, rate_func=rate_functions.wiggle)

        y_bwc = y_vals_1[-1] + (x_vals_2 - 5) * 2 + np.sin(x_vals_2 * 4) * 3
        bwc_graph = axes.plot_line_graph(
            x_vals_2, y_bwc, add_vertex_dots=False, line_color=COLOR_POSITIVE
        ).set_stroke(width=5)

        self.play(
            FadeOut(crash_graph, scale=0.9),
            ReplacementTransform(crash_graph.copy(), bwc_graph),
            run_time=1.5,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.wait(1.5)


class Scene17_DataPipelineFlow(Scene):
    """Structural data flow — chaotic web data snaps into DuckDB lattice and feeds the Fusion Agent."""

    def construct(self):
        title = Text("17. The BWC Pipeline Logic", font_size=32).to_corner(UL)
        self.add(title)

        insight = PhilosophyInsight(
            "Taming Entropy",
            "The web is chaotic entropy.\nDuckDB isn't just storage;\nit is a structural lattice that\nforces chaos into strict,\ncomputable vectors.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.5))

        np.random.seed(4)
        chaos_dots = VGroup(
            *[
                Dot(
                    LEFT * 5 + UP * np.random.uniform(-1, 3) + RIGHT * np.random.uniform(0, 2),
                    color=COLOR_MUTED,
                    radius=0.08,
                )
                for _ in range(40)
            ]
        )
        self.play(FadeIn(chaos_dots, shift=RIGHT * 0.2, lag_ratio=0.05), run_time=1.5)

        db_frame = Rectangle(
            width=2, height=3, stroke_color=COLOR_BLUE, fill_color=COLOR_BLUE, fill_opacity=0.1
        ).move_to(LEFT * 1 + UP * 1)
        lbl = Text("DuckDB Tensor", font_size=18, color=COLOR_BLUE).next_to(db_frame, DOWN)
        self.play(Create(db_frame), FadeIn(lbl))

        grid_spots = []
        for r in range(8):
            for c in range(5):
                grid_spots.append(
                    db_frame.get_corner(UL) + RIGHT * (0.2 + c * 0.4) + DOWN * (0.2 + r * 0.38)
                )

        snap_anims = []
        for i, dot in enumerate(chaos_dots):
            target_dot = Dot(grid_spots[i], color=COLOR_POSITIVE, radius=0.06)
            snap_anims.append(Transform(dot, target_dot))

        self.wait(0.5)
        self.play(*snap_anims, run_time=1.2, rate_func=rate_functions.ease_in_out_back)

        model = (
            Polygon(UP * 0.5, LEFT * 0.5, RIGHT * 0.5, color=COLOR_ACCENT, fill_opacity=0.3)
            .scale(1.5)
            .move_to(RIGHT * 3 + UP * 1)
        )
        model.rotate(-PI / 2)
        m_lbl = Text("Fusion Agent", font_size=16, color=COLOR_ACCENT).next_to(model, DOWN)
        self.play(FadeIn(model, scale=0.8), FadeIn(m_lbl))

        vector_block = Rectangle(
            width=1.8, height=0.3, color=COLOR_POSITIVE, fill_opacity=0.8
        ).move_to(db_frame.get_center())
        self.play(FadeOut(chaos_dots), FadeIn(vector_block))

        self.play(
            vector_block.animate.move_to(model.get_center()).scale(0.5).set_color(COLOR_ACCENT),
            run_time=1,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.play(model.animate.set_fill(opacity=0.8), run_time=0.5)
        self.wait(1.5)
