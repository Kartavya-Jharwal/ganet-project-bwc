"""
Project BWC - Meta Codebase Visualizations
These scenes are explicitly designed to visualize the actual architecture,
modules, and data flow of the Project-BWC repository.
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


class Scene1_ProjectBWC_Architecture(Scene):
    def construct(self):
        title = Text("1. quant_monitor: Core Architecture", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "BWC Codebase",
            "Project BWC is divided into\nspecialized Python modules.\nData flows from Spiders to the\nDatabase, gets parsed into Features,\noptimized by Agents, and Backtested.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        # Create module blocks matching the repo structure
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

        self.play(FadeIn(blocks["quant_monitor/spiders"]))
        self.play(FadeIn(blocks["quant_monitor/data"]))
        self.play(
            GrowArrow(
                Arrow(
                    blocks["quant_monitor/spiders"].get_right(),
                    blocks["quant_monitor/data"].get_left(),
                    color=COLOR_ACCENT,
                )
            )
        )

        self.play(FadeIn(blocks["quant_monitor/features"]))
        self.play(
            GrowArrow(
                Arrow(
                    blocks["quant_monitor/data"].get_bottom(),
                    blocks["quant_monitor/features"].get_top(),
                    color=COLOR_ACCENT,
                )
            )
        )

        self.play(FadeIn(blocks["quant_monitor/agent"]))
        self.play(
            GrowArrow(
                Arrow(
                    blocks["quant_monitor/features"].get_right(),
                    blocks["quant_monitor/agent"].get_left(),
                    color=COLOR_ACCENT,
                )
            )
        )

        self.play(FadeIn(blocks["quant_monitor/backtest"]))
        self.play(
            GrowArrow(
                Arrow(
                    blocks["quant_monitor/agent"].get_bottom(),
                    blocks["quant_monitor/backtest"].get_top(),
                    color=COLOR_ACCENT,
                )
            )
        )

        self.play(FadeIn(blocks["quant_monitor/dashboard"]))
        self.play(
            GrowArrow(
                Arrow(
                    blocks["quant_monitor/backtest"].get_right(),
                    blocks["quant_monitor/dashboard"].get_left(),
                    color=COLOR_ACCENT,
                )
            )
        )
        self.wait(2)


class Scene2_DuckDBSync(Scene):
    def construct(self):
        title = Text("2. quant_monitor.data.duckdb_sync", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "DuckDB Cache",
            "Instead of waiting for slow\nnetwork calls, BWC caches\nmassive market datasets locally\nusing DuckDB, achieving\nin-memory analytic speeds.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        db = Cylinder(
            radius=1, height=2, direction=UP, color=COLOR_PURPLE, fill_opacity=0.3
        ).move_to(LEFT * 2.5)
        db_lbl = Text("portfolio.duckdb", font_size=18).move_to(db.get_center())
        self.play(FadeIn(db, shift=UP), FadeIn(db_lbl))

        cloud = Ellipse(width=3, height=1.5, color=COLOR_BLUE, fill_opacity=0.2).move_to(
            RIGHT * 1.5 + UP * 2
        )
        cloud_lbl = Text("Appwrite API", font_size=18).move_to(cloud.get_center())
        self.play(FadeIn(cloud), FadeIn(cloud_lbl))

        # Data sinking into duckdb
        arrow = Arrow(cloud.get_bottom(), db.get_right(), color=COLOR_WHITE)
        self.play(GrowArrow(arrow))

        for _ in range(5):
            packet = GlowDot(arrow.get_start(), color=COLOR_POSITIVE)
            self.add(packet)
            self.play(MoveAlongPath(packet, arrow), run_time=0.4)
            self.play(FadeOut(packet), run_time=0.1)

        cache_hit = Text("Fast Local Cache Hit!", font_size=24, color=COLOR_POSITIVE).next_to(
            db, DOWN, buff=0.5
        )
        self.play(Write(cache_hit))
        self.wait(1)


class Scene3_FeatureEngineering(Scene):
    def construct(self):
        title = Text("3. quant_monitor.features", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Feature Engine",
            "Raw prices go into features/moving_averages\nand features/volatility. The engine\ntransforms chaos into mathematical\nsignals (like Bollinger bands)\nfor the AI to trade.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[0, 10, 1], y_range=[0, 10, 2], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

        # Raw Data
        np.random.seed(42)
        x_vals = np.linspace(0, 10, 100)
        raw = 5 + x_vals * 0.2 + np.random.normal(0, 1, 100)
        graph_raw = axes.plot_line_graph(x_vals, raw, add_vertex_dots=False, line_color=COLOR_MUTED)
        self.play(Create(graph_raw), run_time=1.5)

        # Output from moving_averages.py and volatility.py
        ma_txt = (
            Text("moving_averages.py", font_size=16, color=COLOR_BLUE)
            .to_corner(UR)
            .shift(DOWN * 1.5 + LEFT * 4)
        )
        vol_txt = Text("volatility.py", font_size=16, color=COLOR_PURPLE).next_to(ma_txt, DOWN)
        self.play(Write(ma_txt), Write(vol_txt))

        # Render smoothed MA and Volatility Bands
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


class Scene4_AgentOptimizer(Scene):
    def construct(self):
        title = Text("4. quant_monitor.agent.optimizer", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Agent Optimizer",
            "The agent balances expected\nreturns against risk in real-time.\nIt receives signals, calculates\noptimal capital allocation,\nand triggers 'alerts.py'.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        # Scale diagram
        beam = Line(LEFT * 2, RIGHT * 2, stroke_width=6).move_to(LEFT * 2.5 + UP * 0.5)
        fulcrum = Polygon(
            UP * 0, LEFT * 0.5, RIGHT * 0.5, color=COLOR_WHITE, fill_opacity=1
        ).move_to(LEFT * 2.5 + DOWN * 0.25)

        lbl_risk = Text(
            "Risk Weight\n(risk_manager.py)", font_size=14, color=COLOR_NEGATIVE
        ).next_to(beam.get_left(), DOWN)
        lbl_ret = Text("Alpha Signal\n(fusion.py)", font_size=14, color=COLOR_POSITIVE).next_to(
            beam.get_right(), DOWN
        )

        self.play(Create(beam), FadeIn(fulcrum), FadeIn(lbl_risk), FadeIn(lbl_ret))

        # Rotate beam to show optimization
        self.play(beam.animate.rotate(0.2), run_time=1)
        self.play(beam.animate.rotate(-0.4), run_time=1.5)
        self.play(beam.animate.rotate(0.2), run_time=1)

        opt_out = Text("optimizer.py -> Allocate 12.4%", font_size=20, color=COLOR_ACCENT).next_to(
            fulcrum, DOWN, buff=1.5
        )
        self.play(Write(opt_out))
        self.wait(1)


class Scene5_BacktestEngine(Scene):
    def construct(self):
        title = Text("5. quant_monitor.backtest.engine", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Simulation Engine",
            "topological_run.py executes\nyears of historical market data\nin seconds. It stress-tests the\nportfolio logic across simulated\nmarket crashes.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[2018, 2024, 1], y_range=[0, 300, 100], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

        x_vals = np.linspace(2018, 2024, 100)
        # S&P Base
        sp500 = 100 * np.exp(0.08 * (x_vals - 2018))
        # Strategy (BWC)
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


class Scene6_ModernMetrics(Scene):
    def construct(self):
        title = Text("6. quant_monitor.backtest.modern_metrics", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Attribution",
            "It's not just about profit.\n'modern_metrics.py' and\n'attribution.py' dissect exactly\n*why* the strategy made money:\nwas it skill, or just luck?",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        box = RoundedRectangle(width=5, height=3, color=COLOR_ACCENT, fill_opacity=0.1).to_edge(
            LEFT, buff=1
        )
        self.play(FadeIn(box))

        m_title = Text("Portfolio Performance Report", font_size=20, color=COLOR_WHITE).move_to(
            box.get_top() + DOWN * 0.4
        )
        sharpe = Text("Sharpe Ratio: 2.14", font_size=18, color=COLOR_POSITIVE).next_to(
            m_title, DOWN, buff=0.4
        )
        sortino = Text("Sortino Ratio: 3.40", font_size=18, color=COLOR_POSITIVE).next_to(
            sharpe, DOWN, buff=0.2
        )
        drawdown = Text("Max Drawdown: -8.4%", font_size=18, color=COLOR_NEGATIVE).next_to(
            sortino, DOWN, buff=0.2
        )

        self.play(Write(m_title))
        self.play(FadeIn(sharpe, shift=RIGHT * 0.2))
        self.play(FadeIn(sortino, shift=RIGHT * 0.2))
        self.play(FadeIn(drawdown, shift=RIGHT * 0.2))

        glow = build_glow(box)
        self.play(FadeIn(glow))
        self.wait(1)


def build_glow(obj):
    return obj.copy().set_color(COLOR_ACCENT).set_stroke(width=10, opacity=0.3)


class Scene7_WebSpiders(Scene):
    def construct(self):
        title = Text("7. quant_monitor.spiders", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Web Spiders",
            "Before any math happens,\nour autonomous 'spiders' crawl\nfinancial websites to extract raw\nmarket data, earnings, and news\nsentiment in real-time.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        spider = Circle(radius=0.5, color=COLOR_ACCENT, fill_opacity=0.5).move_to(LEFT * 4)
        lbl_spider = Text("Scrapy", font_size=16).move_to(spider.get_center())
        self.play(FadeIn(spider), FadeIn(lbl_spider))

        nodes = []
        for i in range(4):
            y_pos = 2 - i * 1.3
            node = Rectangle(width=1.5, height=0.6, color=COLOR_BLUE).move_to(
                LEFT * 0.5 + UP * y_pos
            )
            txt = Text(f"Data Source {i + 1}", font_size=12).move_to(node.get_center())
            nodes.append(VGroup(node, txt))
            self.play(FadeIn(nodes[-1]), run_time=0.2)

        lines = [Line(spider.get_right(), n[0].get_left(), color=COLOR_MUTED) for n in nodes]
        self.play(*[Create(l) for l in lines])

        for _ in range(3):
            for l in lines:
                packet = GlowDot(l.get_end(), color=COLOR_POSITIVE, radius=0.06)
                self.add(packet)
                self.play(MoveAlongPath(packet, Line(l.get_end(), l.get_start())), run_time=0.5)
                self.play(FadeOut(packet), run_time=0.1)

        self.wait(1)


class Scene8_StressTesting(Scene):
    def construct(self):
        title = Text("8. quant_monitor.backtest.stress", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Stress Testing",
            "We don't just optimize for\nthe sunny days. 'stress.py'\ninjects simulated macro shocks\n(like COVID-19 or 2008) to see\nif our portfolio survives.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        axes = (
            Axes(x_range=[0, 10, 2], y_range=[50, 150, 20], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

        x_vals = np.linspace(0, 10, 100)
        # Baseline growth, then massive shock at x=5
        y_normal = 100 + x_vals * 2

        # Creating a sudden shock
        y_shock = []
        for x in x_vals:
            if x < 5:
                y_shock.append(100 + x * 3)
            else:
                y_shock.append((100 + 5 * 3) * 0.6 + (x - 5) * 1)  # 40% drop

        y_bwc = []
        for x in x_vals:
            if x < 5:
                y_bwc.append(100 + x * 2.5)
            else:
                y_bwc.append((100 + 5 * 2.5) * 0.9 + (x - 5) * 2)  # Only 10% drop due to hedge

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

        lbl_bwc = Text("BWC Hedged", font_size=16, color=COLOR_POSITIVE).next_to(
            g_bwc.get_corner(UR), LEFT
        )
        self.play(FadeIn(lbl_bwc))
        self.wait(1)


class Scene9_DynamicAllocation(Scene):
    def construct(self):
        title = Text("9. quant_monitor.backtest.allocation", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Dynamic Allocation",
            "Capital is never static.\nallocation.py shifts weights\ncontinuously. If volatility spikes\nin tech, capital rotates instantly\ninto bonds or cash.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        assets = ["Tech", "Bonds", "Gold", "Crypto", "Cash"]
        colors = [COLOR_PURPLE, COLOR_BLUE, COLOR_ACCENT, COLOR_NEGATIVE, COLOR_POSITIVE]
        initial_w = [0.4, 0.3, 0.1, 0.15, 0.05]

        axes = (
            Axes(x_range=[0, 5, 1], y_range=[0, 0.8, 0.2], x_length=6, y_length=4.5)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(axes))

        bars = VGroup()
        for i, (w, col, name) in enumerate(zip(initial_w, colors, assets, strict=False)):
            bar = Rectangle(
                width=0.6, height=axes.c2p(0, w)[1] - axes.c2p(0, 0)[1], color=col, fill_opacity=0.8
            ).move_to(axes.c2p(i + 0.5, w / 2))
            lbl = Text(name, font_size=14).next_to(bar, DOWN, buff=0.1)
            bars.add(VGroup(bar, lbl))

        self.play(FadeIn(bars), run_time=1.5)

        # Market Shift (New Weights)
        new_w = [0.1, 0.45, 0.2, 0.05, 0.2]
        anims = []
        for i, (w, grp) in enumerate(zip(new_w, bars, strict=False)):
            bar, lbl = grp
            new_height = axes.c2p(0, w)[1] - axes.c2p(0, 0)[1]
            # Create a target bar mapped to the correct new size/position
            target_bar = Rectangle(
                width=0.6, height=new_height, color=bar.get_color(), fill_opacity=0.8
            ).move_to(axes.c2p(i + 0.5, w / 2))
            anims.append(Transform(bar, target_bar))

        txt = (
            Text("Volatility Spike! Reallocating...", color=COLOR_NEGATIVE, font_size=20)
            .to_corner(UR)
            .shift(DOWN * 2 + LEFT * 2)
        )
        self.play(Write(txt))
        self.play(*anims, run_time=2, rate_func=rate_functions.ease_in_out_bounce)
        self.wait(1)


class Scene10_RateLimiter(Scene):
    def construct(self):
        title = Text("10. quant_monitor.data.rate_limiter", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "Rate Limiting",
            "Exchanges strictly limit how\nfast we can request data.\n'rate_limiter.py' acts as a traffic\ncop, intelligently queuing requests\nto avoid IP bans.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        # Sources pushing requests
        reqs = VGroup(
            *[Circle(radius=0.1, color=COLOR_NEGATIVE, fill_opacity=0.8) for _ in range(15)]
        )
        reqs.arrange_in_grid(rows=3, cols=5, buff=0.2).move_to(LEFT * 4 + UP * 1)

        self.play(FadeIn(reqs))

        gate = Rectangle(width=0.5, height=2, color=COLOR_ACCENT, fill_opacity=0.3).move_to(
            LEFT * 2 + UP * 1
        )
        gate_lbl = Text("Rate\nLimiter", font_size=12).move_to(gate.get_center())
        self.play(Create(gate), FadeIn(gate_lbl))

        server = RoundedRectangle(width=2, height=2, color=COLOR_BLUE, fill_opacity=0.2).move_to(
            RIGHT * 1 + UP * 1
        )
        server_lbl = Text("Exchange API", font_size=16).move_to(server.get_center())
        self.play(Create(server), FadeIn(server_lbl))

        q_txt = Text("Queue Queue Queue...", font_size=12, color=COLOR_MUTED).next_to(gate, DOWN)
        self.play(FadeIn(q_txt))

        for i, req in enumerate(reqs):
            # Change color to green when passing
            self.play(req.animate.move_to(gate.get_center()), run_time=0.1)
            self.play(
                req.animate.set_color(COLOR_POSITIVE).move_to(
                    server.get_center()
                    + [np.random.uniform(-0.5, 0.5), np.random.uniform(-0.5, 0.5), 0]
                ),
                run_time=0.2,
            )

        self.wait(1)


class Scene11_DashboardApp(Scene):
    def construct(self):
        title = Text("11. quant_monitor.dashboard.app", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "The Dashboard",
            "All backend complexity converges\nhere. 'app.py' and 'openbb_views.py'\nrender institutional-grade UI,\ndelivering actionable insights\ndirectly to the portfolio manager.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        ui_bg = (
            RoundedRectangle(
                width=6, height=4, corner_radius=0.2, color=COLOR_WHITE, fill_opacity=0.05
            )
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        self.play(Create(ui_bg))

        header = Rectangle(width=6, height=0.5, color=COLOR_WHITE, fill_opacity=0.1).move_to(
            ui_bg.get_top() + DOWN * 0.25
        )
        h_text = Text("BWC Quant Dashboard v1.0", font_size=16, color=COLOR_ACCENT).move_to(
            header.get_center() + LEFT * 1.5
        )
        self.play(Create(header), Write(h_text))

        panel1 = RoundedRectangle(
            width=2.5, height=2.8, color=COLOR_BLUE, fill_opacity=0.1
        ).move_to(ui_bg.get_center() + LEFT * 1.5 + DOWN * 0.2)
        panel2 = RoundedRectangle(
            width=2.5, height=1.3, color=COLOR_PURPLE, fill_opacity=0.1
        ).move_to(ui_bg.get_center() + RIGHT * 1.5 + UP * 0.55)
        panel3 = RoundedRectangle(
            width=2.5, height=1.3, color=COLOR_POSITIVE, fill_opacity=0.1
        ).move_to(ui_bg.get_center() + RIGHT * 1.5 + DOWN * 0.95)

        self.play(FadeIn(panel1), FadeIn(panel2), FadeIn(panel3))

        graph_line = (
            plot_line_graph(
                np.linspace(0, 1, 10),
                np.random.uniform(0, 1, 10),
                add_vertex_dots=False,
                line_color=COLOR_ACCENT,
            )
            .scale(0.8)
            .move_to(panel1.get_center())
        )
        txt2 = Text("Metrics: O.K.", font_size=14).move_to(panel2.get_center())
        txt3 = Text("System: ONLINE", font_size=14, color=COLOR_POSITIVE).move_to(
            panel3.get_center()
        )

        self.play(Create(graph_line), Write(txt2), Write(txt3))
        self.wait(1)


def plot_line_graph(x, y, add_vertex_dots=False, line_color=COLOR_WHITE):
    # Quick helper for Dashboard scene inner plots without Axes
    pts = [np.array([xx, yy, 0]) for xx, yy in zip(x, y, strict=False)]
    return VMobject().set_points_as_corners(pts).set_color(line_color)


class Scene12_AutomatedTesting(Scene):
    def construct(self):
        title = Text("12. tests/test_institutional_stress.py", font_size=32).to_corner(UL)
        self.add(title)

        insight = LaymanInsight(
            "CI/CD Testing",
            "Before any code hits production,\nthe pytest suite rigorously\nvalidates functions. A single\nfailed test blocks deployment,\nensuring zero-defect math.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.2))

        term = (
            RoundedRectangle(width=5.5, height=4, color=COLOR_MUTED, fill_opacity=0.1)
            .to_edge(LEFT, buff=1)
            .shift(DOWN * 0.5)
        )
        term_header = Rectangle(width=5.5, height=0.4, color=COLOR_MUTED, fill_opacity=0.5).move_to(
            term.get_top() + DOWN * 0.2
        )
        dot_r = Dot(color=COLOR_NEGATIVE).move_to(term_header.get_left() + RIGHT * 0.3)
        dot_y = Dot(color=COLOR_ACCENT).move_to(term_header.get_left() + RIGHT * 0.6)
        dot_g = Dot(color=COLOR_POSITIVE).move_to(term_header.get_left() + RIGHT * 0.9)

        self.play(FadeIn(term), FadeIn(term_header), FadeIn(dot_r, dot_y, dot_g))

        tests = [
            "test_allocation.py .......... [100%]",
            "test_config.py .............. [100%]",
            "test_pipeline_cache.py ...... [100%]",
            "test_simulation.py .......... [100%]",
            "test_institutional_stress.py  [100%]",
        ]

        for i, t_str in enumerate(tests):
            t_text = (
                Text("> " + t_str, font_size=14, color=COLOR_POSITIVE, font="monospace")
                .next_to(term_header, DOWN, buff=0.3 + i * 0.4)
                .align_to(term_header, LEFT)
                .shift(RIGHT * 0.3)
            )
            self.play(Write(t_text), run_time=0.4)

        final_res = (
            Text(
                "===== 84 passed in 2.34s =====",
                font_size=16,
                color=COLOR_POSITIVE,
                font="monospace",
            )
            .next_to(term_header, DOWN, buff=0.3 + len(tests) * 0.4 + 0.3)
            .align_to(term_header, LEFT)
            .shift(RIGHT * 0.3)
        )
        self.play(Write(final_res))

        glow = term.copy().set_color(COLOR_POSITIVE).set_stroke(width=8, opacity=0.3)
        self.play(FadeIn(glow))
        self.wait(1)
