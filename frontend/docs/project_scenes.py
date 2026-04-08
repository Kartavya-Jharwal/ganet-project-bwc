"""
Project BWC - Institutional Architecture Visualizations
Hard-coded spatial discipline: every scene respects bounds, uses split-screen composites,
and renders mathematical content as primary narrative (not decoration).
4K 60fps target: 3840×2160 @ 60fps with quintic easing throughout.
"""

import numpy as np
from manim import *

COLOR_BG = "#050505"
COLOR_ACCENT = "#eb5e28"
COLOR_POSITIVE = "#00ff88"
COLOR_NEGATIVE = "#ff3366"
COLOR_MUTED = "#52525b"
COLOR_WHITE = "#f4f4f5"
COLOR_BLUE = "#3b82f6"
COLOR_PURPLE = "#8b5cf6"

config.background_color = COLOR_BG
config.pixel_height = 2160
config.pixel_width = 3840
config.frame_rate = 60

MICRO_SPEED_MULTIPLIER = 1.25
MICRO_INTERACTION_MAX_SECONDS = 1.2
FINAL_FRAME_HOLD_SECONDS = 3.0
LEFT_BOUNDS = (-6.8, -0.3)
RIGHT_BOUNDS = (-0.2, 6.8)
TOP_BOUND = 3.4
BOTTOM_BOUND = -3.5


def smootherstep(t):
    """Quintic Hermite: smooth, physical easing for all micro-interactions."""
    t = np.clip(t, 0.0, 1.0)
    return t * t * t * (t * (t * 6 - 15) + 10)


class BWCTimedScene(Scene):
    """Base: all animations use quintic easing by default. Micro-interactions (≤1.2s) speed up 1.25x."""
    def play(self, *args, **kwargs):
        run_time = kwargs.get("run_time")
        if isinstance(run_time, (int, float)) and run_time <= MICRO_INTERACTION_MAX_SECONDS:
            kwargs["run_time"] = run_time / MICRO_SPEED_MULTIPLIER
            if "rate_func" not in kwargs:
                kwargs["rate_func"] = smootherstep
        return super().play(*args, **kwargs)

    def hold_final_frame(self):
        self.wait(FINAL_FRAME_HOLD_SECONDS)

    def data_packet_stream(self, path, color=COLOR_POSITIVE, duration=0.4, radius=0.06):
        """Animate a glowing data packet along a path with smooth easing."""
        progress = ValueTracker(0.0)
        packet = GlowDot(path.point_from_proportion(0.0), color=color, radius=radius)
        packet.add_updater(lambda m: m.move_to(path.point_from_proportion(progress.get_value())))
        self.add(packet)
        self.play(progress.animate.set_value(1.0), run_time=duration)
        packet.clear_updaters()
        self.play(FadeOut(packet), run_time=0.06)


class GlowDot(VGroup):
    """Layered dot: core + diffuse glow for visual pop."""
    def __init__(self, point, color=COLOR_POSITIVE, radius=0.06, glow_scale=3.5, **kwargs):
        super().__init__(**kwargs)
        self.glow = Dot(point, radius=radius * glow_scale, color=color, fill_opacity=0.15)
        self.core = Dot(point, radius=radius, color=color, fill_opacity=1.0)
        self.add(self.glow, self.core)


def InstitutionalLabel(title, subtitle="", width=3.8):
    """Right-side insight panel: title + subtitle + bordered box."""
    box = RoundedRectangle(
        corner_radius=0.15, width=width, height=2.2, color=COLOR_BLUE, fill_opacity=0.08
    )
    t = Text(title, font_size=20, color=COLOR_ACCENT, weight="bold")
    s = Text(subtitle, font_size=14, line_spacing=1.2, color=COLOR_WHITE)
    group = VGroup(t, s).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    group.move_to(box.get_center() + UP * 0.05)
    return VGroup(box, group).to_edge(RIGHT, buff=0.7).set_z_index(10)


def constrain_to_bounds(obj, left, right, top, bottom):
    """Clip object to absolute bounds."""
    max_width = right - left
    max_height = top - bottom
    
    if obj.width > max_width:
        obj.scale_to_fit_width(max_width * 0.95)
    if obj.height > max_height:
        obj.scale_to_fit_height(max_height * 0.95)
    
    x_shift = 0.0
    y_shift = 0.0
    if obj.get_left()[0] < left:
        x_shift = left - obj.get_left()[0]
    elif obj.get_right()[0] > right:
        x_shift = right - obj.get_right()[0]
    
    if obj.get_top()[1] > top:
        y_shift = top - obj.get_top()[1]
    elif obj.get_bottom()[1] < bottom:
        y_shift = bottom - obj.get_bottom()[1]
    
    if abs(x_shift) > 1e-6 or abs(y_shift) > 1e-6:
        obj.shift(np.array([x_shift, y_shift, 0.0]))
    return obj


class Scene1_ProjectBWC_Architecture(BWCTimedScene):
    def construct(self):
        title = Text("1. BWC: Institutional Architecture", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        # RIGHT: Institutional insight
        insight = InstitutionalLabel(
            "Data Pipeline",
            "Raw market data → Features → Optimization → Backtest → Dashboard"
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        # LEFT: Architecture diagram (split-screen discipline)
        left_anchor = np.array([-3.5, 0.0, 0.0])

        # Vertical module stack with clean spacing
        modules_data = [
            ("Spiders", 2.2, COLOR_BLUE),
            ("DuckDB", 1.0, COLOR_PURPLE),
            ("Features", -0.2, COLOR_BLUE),
            ("Optimizer", -1.4, COLOR_ACCENT),
            ("Backtest", -2.6, COLOR_POSITIVE),
        ]

        blocks = {}
        for name, y_offset, color in modules_data:
            bg = RoundedRectangle(width=2.0, height=0.5, corner_radius=0.1, color=color, fill_opacity=0.15)
            lbl = Text(name, font_size=18, color=COLOR_WHITE, weight="bold")
            grp = VGroup(bg, lbl).move_to(left_anchor + np.array([0, y_offset, 0]))
            blocks[name] = grp
            self.play(FadeIn(grp), run_time=0.35)

        # Data flow arrows
        for i in range(len(modules_data) - 1):
            src = list(blocks.values())[i]
            dst = list(blocks.values())[i + 1]
            arrow = Arrow(src.get_bottom(), dst.get_top(), buff=0.1, color=COLOR_ACCENT, stroke_width=3)
            self.play(Create(arrow), run_time=0.4)
            # Animate data packet
            self.data_packet_stream(arrow, duration=0.5, radius=0.07)

        # Data flow equation (bottom)
        pipeline_eq = MathTex(
            r"\text{Data} \to \text{Features} \to \text{Alpha} \to \text{Strategy}",
            color=COLOR_WHITE,
            font_size=24
        ).move_to(left_anchor + np.array([0, -3.8, 0]))
        self.play(Write(pipeline_eq), run_time=1.0)

        self.hold_final_frame()


class Scene2_DuckDBSync(BWCTimedScene):
    def construct(self):
        title = Text("2. DuckDB: Analytical Cache", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "In-Memory Analytics",
            "Local columnar database eliminates network latency. Analytical queries on cached market data execute in microseconds."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.5, 0.0])

        # Physical database cylinder
        db_cylinder = Cylinder(radius=0.6, height=1.8, direction=UP, color=COLOR_PURPLE, fill_opacity=0.2).move_to(left_anchor)
        db_label = Text("portfolio.duckdb\n(4.2 GB)", font_size=16, color=COLOR_ACCENT, weight="bold").move_to(db_cylinder.get_center())
        self.play(Create(db_cylinder), Write(db_label), run_time=0.9)

        # Data source cloud (top left)
        cloud = Ellipse(width=2.2, height=1.0, color=COLOR_BLUE, fill_opacity=0.1).move_to(left_anchor + np.array([-2.2, 2.0, 0]))
        cloud_txt = Text("Appwrite API\n(Remote)", font_size=14, color=COLOR_WHITE).move_to(cloud.get_center())
        self.play(FadeIn(cloud), Write(cloud_txt), run_time=0.7)

        # Sync arrow downward
        sync_arrow = Arrow(cloud.get_bottom(), db_cylinder.get_top(), buff=0.15, color=COLOR_ACCENT, stroke_width=3)
        self.play(Create(sync_arrow), run_time=0.6)

        # Animated data packet flowing down
        for _ in range(3):
            self.data_packet_stream(sync_arrow, duration=0.45, radius=0.07)

        # Query interface (bottom left)
        query_box = RoundedRectangle(width=2.8, height=0.9, corner_radius=0.1, color=COLOR_BLUE, fill_opacity=0.08).move_to(left_anchor + np.array([0, -2.0, 0]))
        query_txt = MathTex(r"\text{SELECT}\, * \,\text{WHERE} \,\sigma > 0.02", color=COLOR_WHITE, font_size=18).move_to(query_box.get_center())
        self.play(FadeIn(query_box), Write(query_txt), run_time=0.8)

        # Performance metric
        latency = Text("Latency: 2.1ms", font_size=18, color=COLOR_POSITIVE, weight="bold").next_to(query_box, DOWN, buff=0.3)
        self.play(Write(latency), run_time=0.6)

        self.hold_final_frame()


class Scene3_FeatureEngineering(BWCTimedScene):
    def construct(self):
        title = Text("3. Feature Engineering: Signals", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Transform to Signal",
            "Raw OHLCV data → normalized features. Moving averages, volatility bands, momentum oscillators become decision variables."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.2, 0.0])

        # Time series axes
        axes = Axes(
            x_range=[0, 20, 5], y_range=[90, 110, 5],
            x_length=5.5, y_length=3.2, axis_config={"stroke_width": 2, "stroke_color": COLOR_MUTED}
        ).move_to(left_anchor + np.array([0, 0.8, 0]))
        self.play(Create(axes), run_time=0.7)

        # Raw noisy data
        np.random.seed(42)
        x_raw = np.linspace(0, 20, 80)
        y_raw = 100 + 3 * np.sin(x_raw / 3) + np.random.normal(0, 1.2, 80)
        graph_raw = axes.plot_line_graph(x_raw, y_raw, add_vertex_dots=False, line_color=COLOR_MUTED, stroke_width=2)
        self.play(Create(graph_raw), run_time=1.2)

        # Moving average (smoothed)
        y_ma = 100 + 3 * np.sin(x_raw / 3)
        graph_ma = axes.plot_line_graph(x_raw, y_ma, add_vertex_dots=False, line_color=COLOR_BLUE, stroke_width=4)
        
        # Volatility bands
        y_band_up = y_ma + 2.5
        y_band_down = y_ma - 2.5
        graph_up = axes.plot_line_graph(x_raw, y_band_up, add_vertex_dots=False, line_color=COLOR_PURPLE, stroke_width=1)
        graph_down = axes.plot_line_graph(x_raw, y_band_down, add_vertex_dots=False, line_color=COLOR_PURPLE, stroke_width=1)

        # Fill between bands
        band_fill = axes.get_area(
            axes.plot(lambda x: np.clip(100 + 3 * np.sin(x / 3) + 2.5, 90, 110)),
            bounded_graph=axes.plot(lambda x: np.clip(100 + 3 * np.sin(x / 3) - 2.5, 90, 110)),
            color=COLOR_PURPLE, opacity=0.15
        )

        self.play(Create(graph_ma), run_time=1.0)
        self.play(Create(graph_up), Create(graph_down), FadeIn(band_fill), run_time=0.9)

        # Feature equations
        ma_eq = MathTex(r"MA = \frac{1}{w}\sum_{i=0}^{w-1} P_i", color=COLOR_BLUE, font_size=20)
        vol_eq = MathTex(r"\sigma = \sqrt{\frac{1}{n}\sum(P_i - \mu)^2}", color=COLOR_PURPLE, font_size=20)
        
        eqs = VGroup(ma_eq, vol_eq).arrange(DOWN, aligned_edge=LEFT, buff=0.2)
        eqs.move_to(left_anchor + np.array([0, -2.3, 0]))
        constrain_to_bounds(eqs, LEFT_BOUNDS[0], LEFT_BOUNDS[1], TOP_BOUND, BOTTOM_BOUND)
        
        self.play(Write(eqs), run_time=1.0)

        self.hold_final_frame()


class Scene4_AgentOptimizer(BWCTimedScene):
    def construct(self):
        title = Text("4. Portfolio Optimizer: MVO", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Mean-Variance Optimization",
            "Maximize expected return subject to risk constraints. The optimizer solves for optimal capital allocation weights w*."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.5, 0.0])

        # Efficient frontier visualization
        axes = Axes(
            x_range=[0.8, 2.4, 0.4], y_range=[0.04, 0.16, 0.03],
            x_length=5.0, y_length=3.0, axis_config={"stroke_width": 2, "stroke_color": COLOR_MUTED}
        ).move_to(left_anchor + np.array([0, 0.6, 0]))
        
        x_label = axes.get_x_axis_label(r"\sigma_p", edge=DOWN)
        y_label = axes.get_y_axis_label(r"\mathbb{E}[R_p]", edge=LEFT)
        
        self.play(Create(axes), Write(x_label), Write(y_label), run_time=0.8)

        # Frontier curve (parabolic approximation)
        frontier_x = np.linspace(0.8, 2.4, 100)
        frontier_y = 0.06 + 0.025 * (frontier_x - 0.8) ** 0.5
        frontier = axes.plot_line_graph(frontier_x, frontier_y, add_vertex_dots=False, line_color=COLOR_ACCENT, stroke_width=5)
        self.play(Create(frontier), run_time=1.2)

        # Asset clouds spread below frontier
        np.random.seed(42)
        for i in range(8):
            x_pt = np.random.uniform(0.85, 2.3)
            y_pt = np.random.uniform(0.05, 0.095)
            asset_dot = Dot(axes.c2p(x_pt, y_pt), color=COLOR_BLUE, radius=0.08)
            self.play(FadeIn(asset_dot), run_time=0.15)

        # Optimal portfolio point
        opt_x, opt_y = 1.2, 0.095
        opt_dot = Dot(axes.c2p(opt_x, opt_y), color=COLOR_POSITIVE, radius=0.12)
        opt_label = Text("w* (Optimal)", font_size=14, color=COLOR_POSITIVE, weight="bold").next_to(opt_dot, UR, buff=0.1)
        self.play(FadeIn(opt_dot), Write(opt_label), run_time=0.8)

        # Tangent line (capital allocation line)
        cal_start = axes.c2p(0.6, 0.04)
        cal_end = axes.c2p(2.2, 0.14)
        cal_line = Line(cal_start, cal_end, color=COLOR_POSITIVE, stroke_width=2)
        self.play(Create(cal_line), run_time=0.8)

        # Optimization equation
        opt_eq = MathTex(
            r"\max_w \, \mu_p^T w - \frac{\lambda}{2} w^T \Sigma w",
            color=COLOR_ACCENT, font_size=24
        ).move_to(left_anchor + np.array([0, -2.1, 0]))
        self.play(Write(opt_eq), run_time=1.0)

        self.hold_final_frame()


class Scene5_BacktestEngine(BWCTimedScene):
    def construct(self):
        title = Text("5. Backtest Engine: Historical Simulation", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Time Machine Testing",
            "Replay 5+ years of market data. Test strategy logic on historical OHLCV bars. Measure out-of-sample performance."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.3, 0.0])

        # Equity curve axes
        axes = Axes(
            x_range=[2018, 2024, 1], y_range=[80, 220, 30],
            x_length=5.5, y_length=3.2, axis_config={"stroke_width": 2, "stroke_color": COLOR_MUTED}
        ).move_to(left_anchor + np.array([0, 0.8, 0]))
        self.play(Create(axes), run_time=0.7)

        # Benchmark (S&P 500)
        x_bench = np.linspace(2018, 2024, 100)
        y_bench = 100 * np.exp(0.08 * (x_bench - 2018))
        bench_line = axes.plot_line_graph(x_bench, y_bench, add_vertex_dots=False, line_color=COLOR_MUTED, stroke_width=3)
        bench_label = Text("S&P 500", font_size=12, color=COLOR_MUTED).next_to(bench_line, RIGHT, buff=0.2)
        
        # Strategy (with alpha)
        y_strat = 100 * np.exp(0.15 * (x_bench - 2018))
        strat_line = axes.plot_line_graph(x_bench, y_strat, add_vertex_dots=False, line_color=COLOR_POSITIVE, stroke_width=5)
        strat_label = MathTex(r"\text{BWC Strategy: CAGR}=15.2\%", color=COLOR_POSITIVE, font_size=13).next_to(strat_line, RIGHT, buff=0.2)

        self.play(Create(bench_line), Write(bench_label), run_time=1.5)
        self.play(Create(strat_line), Write(strat_label), run_time=2.0)

        # Outperformance area
        outperformance = axes.get_area(
            axes.plot(lambda x: 100 * np.exp(0.15 * (x - 2018))),
            bounded_graph=axes.plot(lambda x: 100 * np.exp(0.08 * (x - 2018))),
            color=COLOR_POSITIVE, opacity=0.15
        )
        self.play(FadeIn(outperformance), run_time=0.9)

        # Performance metrics
        final_x, final_y = 2024, 100 * np.exp(0.15 * 6)
        final_pt = Dot(axes.c2p(final_x, final_y), color=COLOR_POSITIVE, radius=0.1)
        self.play(FadeIn(final_pt), run_time=0.5)

        # Metrics table
        metrics_eq = VGroup(
            MathTex(r"\text{Total Return: } +112\%", color=COLOR_POSITIVE, font_size=18),
            MathTex(r"\text{Sharpe Ratio: } 1.34", color=COLOR_BLUE, font_size=18),
            MathTex(r"\text{Max Drawdown: } -9.2\%", color=COLOR_NEGATIVE, font_size=18)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        metrics_eq.move_to(left_anchor + np.array([0, -2.2, 0]))
        
        self.play(Write(metrics_eq), run_time=1.2)

        self.hold_final_frame()


class Scene6_ModernMetrics(BWCTimedScene):
    def construct(self):
        title = Text("6. Modern Metrics: Attribution", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Brinson Attribution",
            "Decompose returns into allocation effect + selection effect. Understand where alpha came from."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor_attr = np.array([-4.5, 0.5, 0.0])
        left_anchor_risk = np.array([-4.5, -1.8, 0.0])

        # BRINSON ATTRIBUTION PANEL
        attr_axes = Axes(
            x_range=[-0.5, 4.5, 1], y_range=[-0.015, 0.045, 0.015],
            x_length=3.5, y_length=2.2, axis_config={"stroke_width": 1.5, "stroke_color": COLOR_MUTED}
        ).move_to(left_anchor_attr)
        self.play(Create(attr_axes), run_time=0.6)

        # Brinson bars
        categories = ["Alloc", "Select", "Interaction", "Total"]
        values = [0.008, 0.014, -0.002, 0.020]
        colors = [COLOR_BLUE, COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_ACCENT]

        for i, (cat, val, col) in enumerate(zip(categories, values, colors)):
            x_pos = i
            bar = Rectangle(
                width=0.6,
                height=abs(attr_axes.c2p(0, val)[1] - attr_axes.c2p(0, 0)[1]),
                fill_opacity=0.85, color=col
            )
            bar.move_to(attr_axes.c2p(x_pos, val / 2))
            label = Text(cat, font_size=11, color=COLOR_WHITE).next_to(attr_axes.c2p(x_pos, -0.015), DOWN, buff=0.08)
            self.play(FadeIn(bar), Write(label), run_time=0.25)

        # Brinson equation
        brinson_eq = MathTex(
            r"R_a = \sum_i (w_i^P - w_i^B)(r_i^B - r^B) + \sum_i w_i^B(r_i^P - r_i^B)",
            color=COLOR_WHITE, font_size=17
        ).next_to(attr_axes, DOWN, buff=0.3)
        self.play(Write(brinson_eq), run_time=1.0)

        # CVaR / TAIL RISK PANEL
        tail_axes = Axes(
            x_range=[-0.08, 0.08, 0.04], y_range=[0, 1.1, 0.25],
            x_length=3.2, y_length=2.2, axis_config={"stroke_width": 1.5, "stroke_color": COLOR_MUTED}
        ).move_to(left_anchor_risk)
        self.play(Create(tail_axes), run_time=0.6)

        # Gaussian distribution
        x_gauss = np.linspace(-0.08, 0.08, 200)
        y_gauss = np.exp(-0.5 * ((x_gauss - 0.004) / 0.028) ** 2)
        gauss_curve = tail_axes.plot_line_graph(x_gauss, y_gauss, add_vertex_dots=False, line_color=COLOR_BLUE, stroke_width=3)
        self.play(Create(gauss_curve), run_time=0.8)

        # CVaR marker (5th percentile)
        cvar_x = -0.0356
        cvar_line = tail_axes.get_vertical_line(tail_axes.c2p(cvar_x, 1.0), color=COLOR_NEGATIVE, line_func=DashedLine)
        cvar_marker = Dot(tail_axes.c2p(cvar_x, 0), color=COLOR_NEGATIVE, radius=0.09)
        cvar_label = MathTex(r"\mathrm{CVaR}_{5\%}=-3.56\%", color=COLOR_NEGATIVE, font_size=15).next_to(tail_axes, DOWN, buff=0.2)
        
        self.play(Create(cvar_line), FadeIn(cvar_marker), Write(cvar_label), run_time=0.9)

        # Left panel fill for left stage constraint
        left_panel = VGroup(
            attr_axes, brinson_eq, tail_axes, gauss_curve, cvar_line, cvar_marker, cvar_label
        )
        constrain_to_bounds(left_panel, LEFT_BOUNDS[0], LEFT_BOUNDS[1], TOP_BOUND, BOTTOM_BOUND)

        self.hold_final_frame()


class Scene7_WebSpiders(BWCTimedScene):
    def construct(self):
        title = Text("7. Web Spiders: Data Collection", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Distributed Scrapers",
            "Autonomous spiders crawl equity/bond/crypto APIs. Rate-limited requests. Parse OHLCV bars, fundamental data, sentiment."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.3, 0.0])

        # Central spider node
        spider = Circle(radius=0.45, color=COLOR_ACCENT, fill_opacity=0.25).move_to(left_anchor)
        spider_label = MathTex(r"\text{Scrapy}", color=COLOR_ACCENT, font_size=18, weight="bold").move_to(spider.get_center())
        self.play(FadeIn(spider), Write(spider_label), run_time=0.7)

        # Data source nodes radiating out
        sources = [
            ("Yahoo\nFinance", LEFT * 2.8 + UP * 1.5, COLOR_BLUE),
            ("Alpha\nVantage", LEFT * 2.8 + DOWN * 1.5, COLOR_BLUE),
            ("Crypto\nAPIs", RIGHT * 2.2 + UP * 1.2, COLOR_PURPLE),
            ("News\nSentiment", RIGHT * 2.2 + DOWN * 1.2, COLOR_PURPLE),
        ]

        source_groups = []
        for name, pos, col in sources:
            src_box = RoundedRectangle(width=1.5, height=0.7, corner_radius=0.08, color=col, fill_opacity=0.12)
            src_txt = Text(name, font_size=13, color=COLOR_WHITE).move_to(src_box.get_center())
            src_grp = VGroup(src_box, src_txt).move_to(left_anchor + pos)
            source_groups.append(src_grp)
            self.play(FadeIn(src_grp), run_time=0.3)

        # Connection arrows and packets (bidirectional)
        for src_grp in source_groups:
            arrow = Line(spider.get_edge_toward(src_grp.get_edge_toward(spider)), src_grp.get_edge_toward(spider), color=COLOR_MUTED, stroke_width=1.5)
            self.play(Create(arrow), run_time=0.3)
            # Packets flowing (to and from)
            self.data_packet_stream(arrow, duration=0.35, radius=0.06)

        # Data rate equation
        data_rate_eq = MathTex(
            r"\text{Throughput} = 12\,\text{Mbps @ 60fps}",
            color=COLOR_POSITIVE, font_size=20
        ).move_to(left_anchor + np.array([0, -3.0, 0]))
        self.play(Write(data_rate_eq), run_time=0.8)

        self.hold_final_frame()


class Scene8_StressTesting(BWCTimedScene):
    def construct(self):
        title = Text("8. Stress Testing: Tail Events", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Historical Shocks",
            "Inject 2008 crash, COVID drop, rate shocks. Measure portfolio resilience. Does hedging work under pressure?"
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.3, 0.0])

        # Equity curve axes
        axes = Axes(
            x_range=[0, 10, 2], y_range=[30, 130, 20],
            x_length=5.5, y_length=3.2, axis_config={"stroke_width": 2, "stroke_color": COLOR_MUTED}
        ).move_to(left_anchor + np.array([0, 0.8, 0]))
        self.play(Create(axes), run_time=0.7)

        # Unhedged scenario
        x_unhedged = np.linspace(0, 10, 100)
        y_unhedged = np.concatenate([
            100 + 2 * x_unhedged[:50],
            (100 + 2 * 5) * 0.45 + 1.5 * (x_unhedged[50:] - 5)
        ])
        line_unhedged = axes.plot_line_graph(x_unhedged, y_unhedged, add_vertex_dots=False, line_color=COLOR_NEGATIVE, stroke_width=4)

        # Hedged scenario
        y_hedged = np.concatenate([
            100 + 1.8 * x_unhedged[:50],
            (100 + 1.8 * 5) * 0.85 + 2.0 * (x_unhedged[50:] - 5)
        ])
        line_hedged = axes.plot_line_graph(x_unhedged, y_hedged, add_vertex_dots=False, line_color=COLOR_POSITIVE, stroke_width=5)

        # Shock event marker
        shock_line = axes.get_vertical_line(axes.c2p(5, 130), color=COLOR_ACCENT, line_func=DashedLine)
        shock_text = MathTex(r"\text{Shock Event at } t=5", color=COLOR_ACCENT, font_size=16, weight="bold").next_to(shock_line, UP, buff=0.1)

        self.play(Create(line_unhedged), run_time=1.3)
        self.play(Create(shock_line), Write(shock_text), run_time=0.6)
        self.play(Create(line_hedged), run_time=1.3)

        # Loss comparison
        unhedged_losses = abs((100 + 2 * 5) * 0.45 - (100 + 2 * 5))
        hedged_losses = abs((100 + 1.8 * 5) * 0.85 - (100 + 1.8 * 5))
        
        loss_eq = VGroup(
            MathTex(r"\text{Unhedged Loss: } -55.0\%", color=COLOR_NEGATIVE, font_size=18),
            MathTex(r"\text{Hedged Loss: } -15.0\%", color=COLOR_POSITIVE, font_size=18),
            MathTex(r"\text{Protection Benefit: } 40\%", color=COLOR_ACCENT, font_size=18)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
        loss_eq.move_to(left_anchor + np.array([0, -2.2, 0]))

        self.play(Write(loss_eq), run_time=1.2)

        self.hold_final_frame()


class Scene9_DynamicAllocation(BWCTimedScene):
    def construct(self):
        title = Text("9. Dynamic Reallocation", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Real-Time Weights",
            "As market regimes shift, portfolio weights drift from target. Rebalancing triggers maintain risk exposure levels."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.3, 0.0])

        # Asset allocation bar chart
        axes = Axes(
            x_range=[-0.5, 5.5, 1], y_range=[0, 0.6, 0.15],
            x_length=5.0, y_length=3.0, axis_config={"stroke_width": 2, "stroke_color": COLOR_MUTED}
        ).move_to(left_anchor + np.array([0, 0.7, 0]))
        self.play(Create(axes), run_time=0.6)

        # Initial allocation
        assets = ["Equities", "Bonds", "Gold", "Crypto", "Cash"]
        initial_w = [0.40, 0.30, 0.10, 0.15, 0.05]
        colors = [COLOR_BLUE, COLOR_PURPLE, COLOR_ACCENT, COLOR_NEGATIVE, COLOR_POSITIVE]

        bars_initial = VGroup()
        for i, (asset, w, col) in enumerate(zip(assets, initial_w, colors)):
            bar_height = axes.c2p(0, w)[1] - axes.c2p(0, 0)[1]
            bar = Rectangle(width=0.7, height=bar_height, color=col, fill_opacity=0.8)
            bar.move_to(axes.c2p(i, w / 2))
            label = Text(asset, font_size=11, color=COLOR_WHITE).next_to(axes.c2p(i, 0), DOWN, buff=0.12)
            self.play(FadeIn(bar), Write(label), run_time=0.25)
            bars_initial.add(bar)

        self.wait(0.4)

        # Market shift event
        shock_text = MathTex(r"\text{Rate Shock: } +200\,\text{bps}", color=COLOR_NEGATIVE, font_size=18, weight="bold").move_to(left_anchor + np.array([0, 3.2, 0]))
        self.play(Write(shock_text), run_time=0.6)

        # Target reallocation
        target_w = [0.25, 0.50, 0.15, 0.05, 0.05]
        
        # Animate reallocation
        for i, (w_old, w_new, col) in enumerate(zip(initial_w, target_w, colors)):
            old_bar_height = axes.c2p(0, w_old)[1] - axes.c2p(0, 0)[1]
            new_bar_height = axes.c2p(0, w_new)[1] - axes.c2p(0, 0)[1]
            
            new_bar = Rectangle(width=0.7, height=new_bar_height, color=col, fill_opacity=0.8)
            new_bar.move_to(axes.c2p(i, w_new / 2))
            
            self.play(Transform(bars_initial[i], new_bar), run_time=0.5)

        # Rebalance confirmation
        rebalance_eq = MathTex(
            r"w^* = w^{\text{target}} - w^{\text{current}}",
            color=COLOR_ACCENT, font_size=20
        ).next_to(axes, DOWN, buff=0.3)
        self.play(Write(rebalance_eq), run_time=0.8)

        self.hold_final_frame()


class Scene10_RateLimiter(BWCTimedScene):
    def construct(self):
        title = Text("10. Rate Limiting: API Governance", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Queue Management",
            "Exchanges cap request rates (100 req/sec). Queue system prevents IP bans. FIFO dequeuing with exponential backoff."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.5, 0.0])

        # Request source (left)
        source_box = RoundedRectangle(width=1.8, height=2.0, corner_radius=0.1, color=COLOR_BLUE, fill_opacity=0.12)
        source_label = Text("Request\nStream", font_size=13, color=COLOR_WHITE, weight="bold").move_to(source_box.get_center())
        source = VGroup(source_box, source_label).move_to(left_anchor + np.array([-1.8, 0, 0]))
        self.play(FadeIn(source), run_time=0.6)

        # Queue gate (center)
        gate = Rectangle(width=0.8, height=2.2, color=COLOR_ACCENT, fill_opacity=0.15)
        gate_label = MathTex(r"Q(t)", color=COLOR_ACCENT, font_size=20, weight="bold").move_to(gate.get_center())
        gate_full = VGroup(gate, gate_label).move_to(left_anchor + np.array([0, 0, 0]))
        self.play(FadeIn(gate_full), run_time=0.6)

        # Exchange API (right)
        api = RoundedRectangle(width=1.8, height=2.0, corner_radius=0.1, color=COLOR_PURPLE, fill_opacity=0.12)
        api_label = Text("Exchange\nAPI", font_size=13, color=COLOR_WHITE, weight="bold").move_to(api.get_center())
        api_full = VGroup(api, api_label).move_to(left_anchor + np.array([1.8, 0, 0]))
        self.play(FadeIn(api_full), run_time=0.6)

        # Flow arrows
        flow_arrow = Arrow(source.get_right(), gate.get_left(), buff=0.1, stroke_width=2, color=COLOR_MUTED)
        proc_arrow = Arrow(gate_full.get_right(), api_full.get_left(), buff=0.1, stroke_width=2, color=COLOR_POSITIVE)
        self.play(Create(flow_arrow), Create(proc_arrow), run_time=0.5)

        # Animate request packets
        for i in range(12):
            req = Circle(radius=0.06, color=COLOR_BLUE, fill_opacity=0.8).move_to(source.get_right() + np.array([0.3, np.random.uniform(-0.9, 0.9), 0]))
            self.play(FadeIn(req), run_time=0.08)

        self.wait(0.3)

        # Queue packets accumulate
        queue_reqs = []
        for i in range(8):
            qreq = Circle(radius=0.06, color=COLOR_ACCENT, fill_opacity=0.7).move_to(gate.get_center() + np.array([0, 0.8 - i*0.25, 0]))
            queue_reqs.append(qreq)
            self.play(FadeIn(qreq), run_time=0.1)

        # Packets flow through to API
        for qreq in queue_reqs:
            self.play(qreq.animate.move_to(api.get_left() + np.array([-0.3, np.random.uniform(-0.9, 0.9), 0])), run_time=0.2)
            self.play(qreq.animate.set_color(COLOR_POSITIVE), run_time=0.1)

        # Rate limit equation
        rate_eq = MathTex(
            r"\text{Throughput: } \min(R_{\text{request}}, R_{\text{api limit}})",
            color=COLOR_WHITE, font_size=18
        ).move_to(left_anchor + np.array([0, -2.5, 0]))
        self.play(Write(rate_eq), run_time=0.9)

        self.hold_final_frame()


class Scene11_DashboardApp(BWCTimedScene):
    def construct(self):
        title = Text("11. Interactive Dashboard", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Real-Time UI",
            "Plotly dashboards aggregate all backend metrics. Live P&L, risk monitors, trade signals, performance attribution feed manager insights."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.2, 0.0])

        # Dashboard container
        dash_bg = RoundedRectangle(width=6.5, height=4.0, corner_radius=0.15, color=COLOR_MUTED, fill_opacity=0.05)
        dash_header = Rectangle(width=6.5, height=0.45, color=COLOR_WHITE, fill_opacity=0.08)
        dash_header_txt = Text("BWC Manager Dashboard", font_size=16, color=COLOR_ACCENT, weight="bold").move_to(dash_header.get_center())
        
        dashboard = VGroup(dash_bg, dash_header, dash_header_txt).move_to(left_anchor)
        self.play(FadeIn(dashboard), run_time=0.7)

        # Panel 1: P&L
        panel1_bg = RoundedRectangle(width=2.8, height=2.9, corner_radius=0.1, color=COLOR_POSITIVE, fill_opacity=0.08)
        panel1_txt = Text("P&L", font_size=14, color=COLOR_POSITIVE, weight="bold").move_to(panel1_bg.get_top() + DOWN * 0.2)
        
        # Simple line chart in panel1
        p1_axes = Axes(
            x_range=[0, 10, 2], y_range=[0, 100, 25],
            x_length=2.5, y_length=2.0, axis_config={"stroke_width": 0.8, "stroke_color": "#333333"}
        ).scale(0.7).move_to(panel1_bg.get_center() + DOWN * 0.2)
        p1_curve = p1_axes.plot(lambda x: 50 + 3*x, color=COLOR_POSITIVE, stroke_width=2)
        
        panel1 = VGroup(panel1_bg, panel1_txt, p1_axes, p1_curve).move_to(left_anchor + np.array([-1.6, -0.5, 0]))
        self.play(FadeIn(panel1), run_time=0.6)

        # Panel 2: Risk Metrics
        panel2_bg = RoundedRectangle(width=2.8, height=1.35, corner_radius=0.1, color=COLOR_BLUE, fill_opacity=0.08)
        panel2_txt = MathTex(r"\text{Risk: } \sigma=0.018", color=COLOR_BLUE, font_size=14).move_to(panel2_bg.get_center())
        panel2 = VGroup(panel2_bg, panel2_txt).move_to(left_anchor + np.array([1.6, 0.8, 0]))
        self.play(FadeIn(panel2), run_time=0.6)

        # Panel 3: Status
        panel3_bg = RoundedRectangle(width=2.8, height=1.35, corner_radius=0.1, color=COLOR_PURPLE, fill_opacity=0.08)
        status_indicator = Dot(color=COLOR_POSITIVE, radius=0.1).move_to(panel3_bg.get_left() + RIGHT * 0.3 + UP * 0.15)
        status_txt = Text("LIVE", font_size=14, color=COLOR_POSITIVE, weight="bold").next_to(status_indicator, RIGHT, buff=0.15)
        panel3 = VGroup(panel3_bg, status_indicator, status_txt).move_to(left_anchor + np.array([1.6, -0.55, 0]))
        self.play(FadeIn(panel3), run_time=0.6)

        # Real-time metric update animation
        metric_update = MathTex(
            r"\text{Sharpe Ratio: } 1.34 \to 1.35",
            color=COLOR_ACCENT, font_size=16
        ).move_to(left_anchor + np.array([0, -2.6, 0]))
        self.play(Write(metric_update), run_time=0.8)

        self.hold_final_frame()


class Scene12_AutomatedTesting(BWCTimedScene):
    def construct(self):
        title = Text("12. CI/CD: Automated Testing", font_size=36, weight="bold").to_corner(UL)
        self.play(Write(title), run_time=0.8)

        insight = InstitutionalLabel(
            "Test Suite Validation",
            "84 pytest units validate all functions pre-deployment. Every commit triggers type checking, linting, numerical verification."
        )
        self.play(FadeIn(insight, shift=DOWN * 0.3), run_time=0.9)

        left_anchor = np.array([-3.5, 0.5, 0.0])

        # Terminal window
        term_bg = RoundedRectangle(width=6.2, height=3.8, corner_radius=0.1, color=COLOR_MUTED, fill_opacity=0.08)
        term_header = Rectangle(width=6.2, height=0.35, color="#2a2a2a", fill_opacity=0.9)
        
        dot_r = Dot(color=COLOR_NEGATIVE, radius=0.06).move_to(term_header.get_left() + RIGHT * 0.2)
        dot_y = Dot(color=COLOR_ACCENT, radius=0.06).move_to(term_header.get_left() + RIGHT * 0.45)
        dot_g = Dot(color=COLOR_POSITIVE, radius=0.06).move_to(term_header.get_left() + RIGHT * 0.7)
        
        terminal = VGroup(term_bg, term_header, dot_r, dot_y, dot_g).move_to(left_anchor + np.array([0, 0.3, 0]))
        self.play(FadeIn(terminal), run_time=0.6)

        # Test output lines
        test_lines = [
            (r"tests/test_allocation.py", 3, "PASS", COLOR_POSITIVE),
            (r"tests/test_config.py", 2, "PASS", COLOR_POSITIVE),
            (r"tests/test_pipeline_cache.py", 8, "PASS", COLOR_POSITIVE),
            (r"tests/test_simulation.py", 12, "PASS", COLOR_POSITIVE),
            (r"tests/test_stress.py", 14, "PASS", COLOR_POSITIVE),
            (r"tests/test_metrics_attribution.py", 9, "PASS", COLOR_POSITIVE),
        ]

        for i, (test_name, count, status, col) in enumerate(test_lines):
            y_offset = 1.3 - i * 0.45
            line_text = Text(
                f"$ pytest {test_name} [{count} items]", 
                font_size=12, color=COLOR_WHITE, font="monospace"
            ).next_to(terminal.get_top(), DOWN, buff=0.2 + y_offset).align_to(terminal.get_left(), LEFT).shift(RIGHT * 0.3)
            
            status_text = Text(status, font_size=12, color=col, weight="bold", font="monospace").next_to(line_text, RIGHT, buff=0.5)
            
            self.play(Write(line_text), Write(status_text), run_time=0.3)

        self.wait(0.3)

        # Final summary
        summary = Text(
            "===== 84 passed in 2.31s =====",
            font_size=14, color=COLOR_POSITIVE, font="monospace", weight="bold"
        ).next_to(terminal.get_bottom(), UP, buff=0.15)
        
        self.play(Write(summary), run_time=0.8)

        # Success aura
        term_glow = terminal[0].copy().set_fill(opacity=0).set_stroke(color=COLOR_POSITIVE, width=6, opacity=0.25)
        self.play(FadeIn(term_glow), run_time=0.6)

        self.hold_final_frame()
