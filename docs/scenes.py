"""Manim Mathematical Renderings for BWC Portfolio - Epic Cinematic Tier.
Featuring 12 Scenes, Layman Observations, Glow Particles, and Multi-Step Derivations.
"""

import numpy as np
from manim import *

# Institutional Palette
COLOR_BG = "#050505"
COLOR_ACCENT = "#eb5e28"
COLOR_POSITIVE = "#00ff88"
COLOR_NEGATIVE = "#ff3366"
COLOR_MUTED = "#52525b"
COLOR_WHITE = "#f4f4f5"
COLOR_BLUE = "#3b82f6"
COLOR_PURPLE = "#8b5cf6"

config.background_color = COLOR_BG


class GlowDot(VGroup):
    def __init__(self, point, color=COLOR_POSITIVE, radius=0.05, glow_factor=3, **kwargs):
        super().__init__(**kwargs)
        self.center_dot = Dot(point, radius=radius, color=color)
        self.glow = Dot(point, radius=radius * glow_factor, color=color, fill_opacity=0.2)
        self.add(self.glow, self.center_dot)


def LaymanInsight(title_str, body_str):
    box = RoundedRectangle(
        corner_radius=0.2, width=4.2, height=3.0, color=COLOR_BLUE, fill_opacity=0.1
    )
    title = Text(title_str, font_size=20, color=COLOR_ACCENT).move_to(box.get_top() + DOWN * 0.4)
    body = Text(body_str, font_size=16, line_spacing=1.3).next_to(title, DOWN, buff=0.3)
    body.set_color(COLOR_WHITE)
    return VGroup(box, title, body).to_edge(RIGHT, buff=0.5).set_z_index(10)


class Scene1_GeometricBrownianMotion(MovingCameraScene):
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
            Axes(x_range=[0, 100, 20], y_range=[0, 200, 50], x_length=5, y_length=4)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 1)
        )
        self.play(Create(axes))

        lines = VGroup()
        np.random.seed(42)
        for _ in range(12):
            path = [100]
            for _ in range(80):
                path.append(
                    path[-1]
                    * np.exp((0.001 - 0.5 * 0.005) * 1 + np.sqrt(0.005) * np.random.normal())
                )
            c = axes.plot_line_graph(
                x_values=np.arange(81), y_values=path, line_color=COLOR_BLUE, add_vertex_dots=False
            ).set_stroke(opacity=0.4)
            p = GlowDot(axes.c2p(0, 100), color=COLOR_POSITIVE)
            self.play(MoveAlongPath(p, c), run_time=0.8, rate_func=linear)
            lines.add(c)
            self.play(FadeOut(p), run_time=0.1)

        bell = axes.plot(
            lambda x: 100 + 40 * np.exp(-0.5 * ((x - 100) / 20) ** 2), color=COLOR_ACCENT
        )
        self.play(Create(bell), rate_func=rate_functions.ease_in_out_sine)
        self.wait(1)


class Scene2_MarkowitzEfficientFrontier(MovingCameraScene):
    def construct(self):
        title = Text("2. Modern Portfolio Theory", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "You don't want to just pick\nstocks randomly. You want to\nfind the absolute boundary\n(the optimal edge) where\nrisk is minimized for every\ndrop of return.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[0, 0.4, 0.1], y_range=[0, 0.25, 0.05], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

        dots = VGroup()
        np.random.seed(99)
        for _ in range(250):
            vol = np.random.uniform(0.05, 0.35)
            max_r = 0.15 * np.sqrt((vol - 0.05) / 0.2) if vol > 0.05 else 0
            if max_r > 0:
                dots.add(
                    Dot(
                        axes.c2p(vol, np.random.uniform(0.01, max_r)),
                        color=COLOR_MUTED,
                        radius=0.03,
                    )
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


class Scene3_CapitalMarketLine(Scene):
    def construct(self):
        title = Text("3. Capital Market Line & Tangency", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "By holding some cash alongside\nthe optimal portfolio, we can\nslide up and down a perfectly\nstraight line, escaping the\nlimitations of stocks alone.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[0, 0.3, 0.1], y_range=[0, 0.2, 0.05], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        rf_dot = Dot(axes.c2p(0, 0.02), color=COLOR_WHITE)
        frontier = axes.plot(
            lambda x: 0.15 * np.sqrt((x - 0.05) / 0.2), x_range=[0.05, 0.3], color=COLOR_POSITIVE
        )

        self.play(Create(axes), Create(frontier), FadeIn(rf_dot))

        tracker = ValueTracker(0.3)

        def get_cml():
            x = tracker.get_value()
            y = 0.15 * np.sqrt((x - 0.05) / 0.2)
            return Line(
                rf_dot.get_center(),
                axes.c2p(x + 0.1, y + (y - 0.02) / (x) * (0.1)),
                color=COLOR_ACCENT,
            ).set_z_index(3)

        self.add(always_redraw(get_cml))
        self.play(
            tracker.animate.set_value(0.1), run_time=3, rate_func=rate_functions.ease_in_out_sine
        )
        self.wait()


class Scene4_AlphaBetaOrthogonality(Scene):
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

        self.play(Create(v_beta))
        self.play(Create(v_alpha))
        self.wait(1)


class Scene5_ValueAtRiskSweep(Scene):
    def construct(self):
        title = Text("5. Conditional Value at Risk (CVaR)", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Standard 'VaR' tells you where\nthe cliff edge is. 'CVaR'\nactually measures the average\ndepth of the fall once you go\nover the cliff.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[-4, 4, 1], y_range=[0, 0.5, 0.1], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        curve = axes.plot(
            lambda x: 1 / (np.sqrt(2 * np.pi)) * np.exp(-0.5 * x**2), color=COLOR_WHITE
        )
        self.play(Create(axes), Create(curve))

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
        self.play(Create(line))
        self.wait(1)


class Scene6_KellyCriterionCalculus(Scene):
    def construct(self):
        title = Text("6. The Kelly Parabola", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "If you bet cautiously, you\ngrow slowly. But if you\nbet past the optimal peak,\nvolatility destroys you and\nyou mathematically go broke.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[0, 1, 0.2], y_range=[0, 0.1, 0.02], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        curve = axes.plot(
            lambda x: 0.15 * x - 0.5 * (0.2) * x**2, x_range=[0, 1], color=COLOR_POSITIVE
        )
        self.play(Create(axes), Create(curve))

        tracker = ValueTracker(0.1)
        tangent = always_redraw(
            lambda: axes.plot(
                lambda x: (
                    (0.15 - 0.2 * tracker.get_value()) * (x - tracker.get_value())
                    + (0.15 * tracker.get_value() - 0.5 * (0.2) * tracker.get_value() ** 2)
                ),
                color=COLOR_ACCENT,
                x_range=[tracker.get_value() - 0.2, tracker.get_value() + 0.2],
            )
        )

        self.add(tangent)
        self.play(
            tracker.animate.set_value(0.75), run_time=3, rate_func=rate_functions.ease_in_out_sine
        )
        self.wait(1)


class Scene7_CovarianceGeometry(ThreeDScene):
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
        axes = ThreeDAxes()
        self.add(axes)

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


class Scene8_YieldCurveDynamics(Scene):
    def construct(self):
        title = Text("8. Dynamic Yield Curve", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Normally, locking money up\nlonger pays more. When this\ncurve inverts, the institutional\nbond market is flashing a\nmassive recession warning.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[0, 30, 5], y_range=[0, 6, 1], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

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
        self.add(curve)
        self.play(t.animate.set_value(1), run_time=3, rate_func=rate_functions.ease_in_out_sine)
        self.wait(1)


class Scene9_OptionsVolatilitySmile(Scene):
    def construct(self):
        title = Text("9. Options Volatility Smile", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Market actors are terrified\nof sudden crashes. Therefore,\nthey chronically overprice\ninsurance against massive drops,\nbending the volatility curve.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[80, 120, 10], y_range=[0.1, 0.4, 0.1], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

        t = ValueTracker(0)
        smile = always_redraw(
            lambda: axes.plot(
                lambda x: 0.15 + interpolate(0.0005, 0.002, t.get_value()) * (x - 100) ** 2,
                color=COLOR_PURPLE,
            )
        )
        self.add(smile)
        self.play(t.animate.set_value(1), run_time=2, rate_func=rate_functions.ease_in_out_cubic)
        self.wait(1)


class Scene10_RiskParityEquilibrium(Scene):
    def construct(self):
        title = Text("10. Risk Parity Constraints", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Allocating 50/50 capital isn't\ntrue balance if one asset is\nten times more volatile.\nTrue parity balances the raw\nrisk weight, not the dollar.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        a1 = VGroup(
            Circle(radius=2, color=COLOR_ACCENT, fill_opacity=0.5), Text("Asset A\nLow Vol")
        ).shift(LEFT * 3.5 + DOWN * 0.5)
        a2 = VGroup(
            Circle(radius=0.5, color=COLOR_BLUE, fill_opacity=0.5),
            Text("Asset B\nHigh Vol", font_size=16),
        ).shift(LEFT * 0.5 + DOWN * 0.5)

        self.play(FadeIn(a1), FadeIn(a2))
        self.play(
            a1[0].animate.scale(0.7),
            a2[0].animate.scale(2.8),
            run_time=2,
            rate_func=rate_functions.ease_in_out_sine,
        )
        self.wait(1)


class Scene11_JumpDiffusionPoisson(Scene):
    def construct(self):
        title = Text("11. Brownian Motion w/ Poisson Shocks", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Real markets don't move in\nsmooth continuous lines. They\nsuffer massive, unpredictable\nlightning crashes (jumps) that\nbreak standard risk models.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[0, 10, 1], y_range=[0, 20, 5], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

        np.random.seed(11)
        y = [10]
        for i in range(1, 100):
            y.append(
                y[-1] + 0.01 + np.random.normal(0, 0.2) + (-3.0 if np.random.rand() < 0.03 else 0)
            )

        g = axes.plot_line_graph(
            np.linspace(0, 10, 100), y, add_vertex_dots=False, line_color=COLOR_NEGATIVE
        )
        self.play(Create(g, run_time=3, rate_func=linear))
        self.wait(1)


class Scene12_OrderBookImbalance(Scene):
    def construct(self):
        title = Text("12. LOB Liquidity Microstructure", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Before a price moves, the\nunderlying supply (Asks) and\ndemand (Bids) shift heavily.\nImbalances here dictate the\nmicro-direction of the price.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        t = ValueTracker(0.5)
        bids = always_redraw(
            lambda: Rectangle(
                width=1.5, height=3 * t.get_value(), color=COLOR_POSITIVE, fill_opacity=0.8
            ).shift(LEFT * 3.5, DOWN * (1.5 - 1.5 * t.get_value()))
        )
        asks = always_redraw(
            lambda: Rectangle(
                width=1.5, height=3 * (1 - t.get_value()), color=COLOR_NEGATIVE, fill_opacity=0.8
            ).shift(LEFT * 1.5, DOWN * (1.5 - 1.5 * (1 - t.get_value())))
        )

        lbl_b = Text("Bids", font_size=20, color=COLOR_POSITIVE).shift(LEFT * 3.5 + DOWN * 2)
        lbl_a = Text("Asks", font_size=20, color=COLOR_NEGATIVE).shift(LEFT * 1.5 + DOWN * 2)

        self.play(
            Create(Line(LEFT * 4.5, LEFT * 0.5, color=COLOR_WHITE).shift(DOWN * 1.5)),
            FadeIn(lbl_b),
            FadeIn(lbl_a),
        )
        self.add(bids, asks)

        self.play(t.animate.set_value(0.2), run_time=1)
        self.play(t.animate.set_value(0.8), run_time=1.5)
        self.play(t.animate.set_value(0.5), run_time=1)
        self.wait(1)


class Scene13_TickerHeatmap(Scene):
    def construct(self):
        title = Text("13. Market Heatmap & Tickers", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "A heatmap strips away the noise\nof individual charts and shows\nthe systemic mood of the market\nin a single glance. Green is\ngreed, red is fear.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        tickers = [
            "AAPL",
            "MSFT",
            "NVDA",
            "TSLA",
            "AMZN",
            "GOOG",
            "META",
            "AMD",
            "BRK.B",
            "JPM",
            "V",
            "JNJ",
        ]
        np.random.seed(42)
        returns = np.random.uniform(-0.05, 0.05, len(tickers))

        grid = VGroup()
        for i, (tick, ret) in enumerate(zip(tickers, returns, strict=False)):
            color = COLOR_POSITIVE if ret > 0 else COLOR_NEGATIVE
            opacity = min(abs(ret) * 20, 1.0)  # Scale opacity by return magnitude

            box = Rectangle(
                width=1.5, height=1.0, stroke_color=COLOR_BG, fill_color=color, fill_opacity=opacity
            )
            txt = Text(tick, font_size=16, color=COLOR_WHITE)
            val = Text(f"{ret * 100:+.1f}%", font_size=12, color=COLOR_WHITE).next_to(
                txt, DOWN, buff=0.1
            )

            cell = VGroup(box, txt, val)
            grid.add(cell)

        grid.arrange_in_grid(rows=3, cols=4, buff=0.1).to_edge(LEFT, buff=1).shift(DOWN * 0.5)

        self.play(
            LaggedStart(*[FadeIn(cell, scale=0.8) for cell in grid], lag_ratio=0.1), run_time=3
        )
        self.wait(1)

        # Pulse updates
        new_returns = returns + np.random.normal(0, 0.02, len(tickers))
        anims = []
        for cell, ret in zip(grid, new_returns, strict=False):
            color = COLOR_POSITIVE if ret > 0 else COLOR_NEGATIVE
            opacity = min(abs(ret) * 20, 1.0)
            val = Text(f"{ret * 100:+.1f}%", font_size=12, color=COLOR_WHITE).move_to(
                cell[2].get_center()
            )
            anims.append(cell[0].animate.set_fill(color=color, opacity=opacity))
            anims.append(Transform(cell[2], val))

        self.play(*anims, run_time=1.5)
        self.wait(1)


class Scene14_SignalExtraction(Scene):
    def construct(self):
        title = Text("14. Signal Extraction (Moving Averages)", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Raw financial data is extremely\nnoisy, bouncing wildly day to\nday. Signal extraction filters out\nthe static, revealing the true\nunderlying trend we can trade.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[0, 10, 1], y_range=[0, 10, 2], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

        # Noisy signal
        np.random.seed(1)
        x_vals = np.linspace(0, 10, 200)
        true_signal = 5 + 2 * np.sin(x_vals)
        noise = np.random.normal(0, 1.0, len(x_vals))
        noisy_signal = true_signal + noise

        noisy_graph = axes.plot_line_graph(
            x_vals, noisy_signal, add_vertex_dots=False, line_color=COLOR_MUTED
        ).set_stroke(width=1)
        self.play(Create(noisy_graph), run_time=2)

        # Extracted signal (Glowing)
        clean_graph = axes.plot_line_graph(
            x_vals, true_signal, add_vertex_dots=False, line_color=COLOR_ACCENT
        ).set_stroke(width=4)
        glow = axes.plot_line_graph(
            x_vals, true_signal, add_vertex_dots=False, line_color=COLOR_ACCENT
        ).set_stroke(width=12, opacity=0.3)

        self.play(Create(clean_graph), FadeIn(glow), run_time=3)
        self.wait(1)


class Scene15_SystemArchitecture(Scene):
    def construct(self):
        title = Text("15. BWC: Systems & Architecture", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "A quant fund isn't just math;\nit's a highly engineered software\nmachine. Data streams in,\nfeatures are extracted, AI agents\noptimize, and dashboards report.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        def make_node(text, color, pos):
            box = RoundedRectangle(
                corner_radius=0.2, width=2.4, height=1.0, color=color, fill_opacity=0.2
            ).move_to(pos)
            lbl = Text(text, font_size=16, color=COLOR_WHITE).move_to(box.get_center())
            return VGroup(box, lbl)

        n_data = make_node("Data & Spiders", COLOR_BLUE, LEFT * 4.5 + UP * 1)
        n_db = make_node("Appwrite / DuckDB", COLOR_BLUE, LEFT * 1.5 + UP * 1)
        n_feat = make_node("Feature Engine", COLOR_PURPLE, LEFT * 3 + DOWN * 1)
        n_agent = make_node("Agent / Optimizer", COLOR_ACCENT, LEFT * 0 + DOWN * 1)
        n_dash = make_node("Dashboard (UI)", COLOR_POSITIVE, RIGHT * 1.5 + UP * 0)

        # Draw directed arrows
        a1 = Arrow(n_data.get_right(), n_db.get_left(), buff=0.1, color=COLOR_WHITE)
        a2 = Arrow(n_db.get_bottom(), n_feat.get_top(), buff=0.1, color=COLOR_WHITE)
        a3 = Arrow(n_feat.get_right(), n_agent.get_left(), buff=0.1, color=COLOR_WHITE)
        a4 = Arrow(n_agent.get_right(), n_dash.get_bottom(), buff=0.1, color=COLOR_WHITE)
        a5 = Arrow(n_db.get_right(), n_dash.get_left(), buff=0.1, color=COLOR_WHITE)

        self.play(FadeIn(n_data, shift=RIGHT * 0.5))
        self.play(GrowArrow(a1), FadeIn(n_db, shift=RIGHT * 0.5))
        self.play(GrowArrow(a2), FadeIn(n_feat, shift=RIGHT * 0.5))
        self.play(GrowArrow(a3), FadeIn(n_agent, shift=RIGHT * 0.5))
        self.play(GrowArrow(a4), GrowArrow(a5), FadeIn(n_dash, shift=RIGHT * 0.5))

        # Flow data particles
        particle = GlowDot(n_data.get_left(), color=COLOR_POSITIVE, radius=0.08)
        self.add(particle)
        self.play(
            MoveAlongPath(particle, Line(n_data.get_center(), n_db.get_center())), run_time=0.5
        )
        self.play(
            MoveAlongPath(particle, Line(n_db.get_center(), n_feat.get_center())), run_time=0.5
        )
        self.play(
            MoveAlongPath(particle, Line(n_feat.get_center(), n_agent.get_center())), run_time=0.5
        )
        self.play(
            MoveAlongPath(particle, Line(n_agent.get_center(), n_dash.get_center())), run_time=0.5
        )
        self.play(FadeOut(particle))
        self.wait()


class Scene16_DataPipeline(Scene):
    def construct(self):
        title = Text("16. The Data Pipeline Engine", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "To make lightning-fast decisions,\nheavy raw data is pulled from the\nweb, cached in memory via DuckDB,\nand synchronized directly to our\nAppwrite cloud backend.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        # Funnels
        raw_data = VGroup(
            *[
                Text("10101", font_size=12, color=COLOR_MUTED).move_to(
                    LEFT * 5 + UP * (2 - i * 0.5)
                )
                for i in range(5)
            ]
        )
        self.play(FadeIn(raw_data))

        funnel = Polygon(
            LEFT * 4 + UP * 2.5,
            LEFT * 4 + DOWN * 1.5,
            LEFT * 2 + DOWN * 0.5,
            LEFT * 2 + UP * 1.5,
            color=COLOR_ACCENT,
            fill_opacity=0.1,
        )
        funnel_lbl = Text("Rate Limiter\n& Cache", font_size=14, color=COLOR_ACCENT).move_to(
            funnel.get_center()
        )
        self.play(Create(funnel), FadeIn(funnel_lbl))

        duck_db = Cylinder(
            radius=0.8, height=1.5, direction=UP, color=COLOR_BLUE, fill_opacity=0.3
        ).move_to(LEFT * 0.5 + UP * 0.5)
        duck_lbl = Text("DuckDB", font_size=16).move_to(duck_db.get_center())

        appwrite = Cylinder(
            radius=0.8, height=1.5, direction=UP, color=COLOR_PURPLE, fill_opacity=0.3
        ).move_to(RIGHT * 1.5 + DOWN * 1.5)
        app_lbl = Text("Appwrite\nSync", font_size=16).move_to(appwrite.get_center())

        self.play(FadeIn(duck_db), FadeIn(duck_lbl))
        self.play(FadeIn(appwrite), FadeIn(app_lbl))

        # Animate data compaction
        for rd in raw_data:
            self.play(
                rd.animate.move_to(duck_db.get_center()).set_color(COLOR_POSITIVE).scale(0.5),
                run_time=0.2,
            )

        self.play(FadeOut(raw_data))
        connect_arrow = Arrow(duck_db.get_bottom(), appwrite.get_top(), color=COLOR_WHITE)
        self.play(GrowArrow(connect_arrow))

        flow_packet = GlowDot(duck_db.get_center(), color=COLOR_BLUE)
        self.play(MoveAlongPath(flow_packet, connect_arrow), run_time=1)
        self.play(appwrite.animate.set_fill(COLOR_POSITIVE, opacity=0.5))
        self.wait(1)


class Scene17_TradingStrategyLogic(Scene):
    def construct(self):
        title = Text("17. Agent Trading Strategy Logic", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Investor Insight",
            "Human emotions destroy wealth.\nOur mathematical agents follow\ncold, hard logic: check risks,\nscore signals, and optimize sizes\nbefore executing any trade.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        # Logic flowchart
        dec1 = (
            Polygon(UP * 1, LEFT * 1.5, DOWN * 1, RIGHT * 1.5, color=COLOR_BLUE, fill_opacity=0.2)
            .scale(0.8)
            .move_to(LEFT * 4 + UP * 1)
        )
        lbl1 = Text("Signal >\nThreshold?", font_size=14, color=COLOR_WHITE).move_to(
            dec1.get_center()
        )

        box_yes = RoundedRectangle(
            width=2, height=1, color=COLOR_POSITIVE, fill_opacity=0.2
        ).move_to(LEFT * 1 + UP * 2.5)
        lbl_y = Text("Risk Manager", font_size=16, color=COLOR_POSITIVE).move_to(
            box_yes.get_center()
        )

        box_no = RoundedRectangle(
            width=2, height=1, color=COLOR_NEGATIVE, fill_opacity=0.2
        ).move_to(LEFT * 1 + DOWN * 0.5)
        lbl_n = Text("Hold / Ignore", font_size=16, color=COLOR_NEGATIVE).move_to(
            box_no.get_center()
        )

        box_opt = RoundedRectangle(width=2, height=1, color=COLOR_ACCENT, fill_opacity=0.2).move_to(
            RIGHT * 1.5 + UP * 1
        )
        lbl_opt = Text("Allocation\nOptimizer", font_size=16, color=COLOR_ACCENT).move_to(
            box_opt.get_center()
        )

        self.play(Create(dec1), FadeIn(lbl1))

        a_yes = Arrow(dec1.get_right(), box_yes.get_left(), path_arc=-0.5, color=COLOR_WHITE)
        txt_yes = Text("Yes", font_size=12).next_to(a_yes, UP, buff=0.1)
        self.play(GrowArrow(a_yes), FadeIn(txt_yes), FadeIn(box_yes), FadeIn(lbl_y))

        a_no = Arrow(dec1.get_bottom(), box_no.get_left(), path_arc=0.5, color=COLOR_WHITE)
        txt_no = Text("No", font_size=12).next_to(a_no, RIGHT, buff=0.1)
        self.play(GrowArrow(a_no), FadeIn(txt_no), FadeIn(box_no), FadeIn(lbl_n))

        a_opt = Arrow(box_yes.get_right(), box_opt.get_top(), path_arc=-0.5, color=COLOR_WHITE)
        txt_pass = Text("Approved", font_size=12, color=COLOR_POSITIVE).next_to(a_opt, UP, buff=0.1)
        self.play(GrowArrow(a_opt), FadeIn(txt_pass), FadeIn(box_opt), FadeIn(lbl_opt))

        # Simulate execution pulse
        pulse = GlowDot(box_opt.get_center(), color=COLOR_ACCENT, glow_factor=6, radius=0.2)
        self.play(FadeIn(pulse, scale=2))
        self.play(FadeOut(pulse))
        self.wait(1)


class Scene18_ProjectMetaVisualization(ThreeDScene):
    def construct(self):
        title = Text("18. Project BWC: The Meta Vision", font_size=32).to_corner(UL)
        self.add_fixed_in_frame_mobjects(title)

        insight = LaymanInsight(
            "Investor Insight",
            "All the data pipelines, trading\nagents, complex math, and risk\nmodels coalesce into one singular\ngoal: maximizing performance\nand building institutional wealth.",
        )
        insight.to_corner(DR).shift(UP * 0.5 + LEFT * 0.5)
        self.add_fixed_in_frame_mobjects(insight)
        self.play(FadeIn(insight))

        self.set_camera_orientation(phi=65 * DEGREES, theta=30 * DEGREES)

        # Center core (The Portfolio)
        core = Sphere(radius=1.0, resolution=(20, 20)).set_color(COLOR_ACCENT)
        self.play(Create(core))

        orbits = VGroup()
        for r, color in zip([2, 3, 4], [COLOR_BLUE, COLOR_PURPLE, COLOR_POSITIVE], strict=False):
            orbit = Circle(radius=r, color=color).set_stroke(opacity=0.3)
            # Make it 3D by rotating it to lay flat on the XY plane
            orbit.rotate(PI / 2, axis=RIGHT)
            orbits.add(orbit)

        self.play(Create(orbits))

        # Add nodes representing the project
        labels = ["Appwrite", "DuckDB", "Agents", "Backtest", "Pipelines", "Risk Models"]
        nodes = VGroup()
        for i, lbl_txt in enumerate(labels):
            orbit_idx = i % 3
            angle = i * (TAU / len(labels))
            r = 2 + orbit_idx
            x, y = r * np.cos(angle), r * np.sin(angle)

            node = GlowDot([x, y, 0], color=COLOR_WHITE, radius=0.1)
            # Force orientation to face camera for labels if this was a 2D scene, but in 3D we skip labels to keep it clean, just dots
            nodes.add(node)

        self.play(FadeIn(nodes))

        self.begin_ambient_camera_rotation(rate=0.3)
        self.wait(5)
        self.stop_ambient_camera_rotation()
