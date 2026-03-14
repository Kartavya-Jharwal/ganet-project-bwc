"""
Project BWC - 3B1B Philosophical Cinematic Enhancements
"The visuals are the logic."
Uses spatial metaphors, rhythm, semantic color shifts, and geometric intuition.
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


def PhilosophyInsight(title_str, body_str):
    box = RoundedRectangle(
        corner_radius=0.1, width=4.5, height=2.8, color=COLOR_MUTED, fill_opacity=0.05
    )
    title = Text(title_str, font_size=22, color=COLOR_WHITE).move_to(box.get_top() + DOWN * 0.5)
    body = Text(body_str, font_size=16, line_spacing=1.4).next_to(title, DOWN, buff=0.4)
    body.set_color(COLOR_MUTED)
    return VGroup(box, title, body).to_edge(RIGHT, buff=0.5).set_z_index(10)


# =======================================================
# 1. THE STOCHASTIC METAPHOR (Animating Possibility, Not Paths)
# =======================================================
class Vis_TheStochasticVoid(Scene):
    def construct(self):
        title = Text("1. The Geometry of Unknowns (SDEs)", font_size=32).to_corner(UL)
        self.add(title)

        insight = PhilosophyInsight(
            "Visualizing the Void",
            "We don't predict a single future.\nWe simulate thousands of ghostly\nrealities. Where the paths overlap\nand turn bright, probability lives.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.5))

        # 1. Concrete Example: A single fragile path.
        axes = Axes(x_range=[0, 10, 2], y_range=[0, 200, 50], x_length=6, y_length=4.5).to_edge(
            LEFT, buff=1
        )
        self.play(Create(axes, run_time=1.5, rate_func=rate_functions.ease_out_expo))

        np.random.seed(42)

        def get_path():
            p = [100]
            for _ in range(50):
                p.append(p[-1] * np.exp((0.02 - 0.5 * 0.05) + np.sqrt(0.05) * np.random.normal()))
            return p

        # Fade in the first path slowly
        first_path_y = get_path()
        first_path = axes.plot_line_graph(
            np.linspace(0, 10, 51), first_path_y, add_vertex_dots=False, line_color=COLOR_MUTED
        ).set_stroke(width=2)

        # When moving an object along a path that is strictly a LineGraph, we should use the actual function or a ValueTracker.
        # But an elegant way is to use UpdateFromFunc or ValueTracker to avoid the 'no points' issue with MoveAlongPath on LineGraphs.
        dot = GlowDot(axes.c2p(0, 100), color=COLOR_WHITE)
        self.add(dot)

        # Let's cleanly animate it using Create on the path
        self.play(Create(first_path), run_time=2, rate_func=linear)

        # 2. Generalization: The explosion of possibilities
        paths = VGroup()
        hex_colors = [COLOR_BLUE, COLOR_PURPLE, COLOR_ACCENT, COLOR_WHITE]
        for i in range(40):
            color = np.random.choice(hex_colors)
            paths.add(
                axes.plot_line_graph(
                    np.linspace(0, 10, 51), get_path(), add_vertex_dots=False, line_color=color
                ).set_stroke(width=1, opacity=0.15)
            )

        # Rhythm: Sudden explosion of paths matching the 'Aha' moment
        self.play(
            LaggedStart(*[Create(p) for p in paths], lag_ratio=0.02),
            run_time=3,
            rate_func=rate_functions.ease_out_cubic,
        )

        # 3. Formal Summary: The distribution bell reveals the true structure
        bell = axes.plot(
            lambda x: 100 + 60 * np.exp(-0.5 * ((x - 100) / 25) ** 2),
            x_range=[0, 200],
            use_smoothing=True,
            color=COLOR_ACCENT,
        )
        # We mathematically pivot the axes to look at the distribution from the side
        bell.rotate(PI / 2, axis=IN, about_point=axes.c2p(10, 100))
        bell.shift(RIGHT * 1)

        self.play(Create(bell), run_time=2, rate_func=rate_functions.ease_in_out_sine)

        # Color Shift -> Meaning: Accent color means "Calculated Risk Boundary"
        fill = axes.get_area(
            bell, x_range=[0, 60], color=COLOR_NEGATIVE, opacity=0.6
        )  # The tail risk

        # Wait, get_area won't work perfectly on a rotated bell without complex transforms.
        # Instead, we'll draw a literal line indicating the risk threshold.
        threshold = axes.get_horizontal_line(axes.c2p(10, 60), color=COLOR_NEGATIVE).set_stroke(
            width=3
        )
        self.play(
            Create(threshold),
            paths.animate.set_color(COLOR_MUTED).set_stroke(opacity=0.05),
            run_time=1.5,
        )
        self.wait(1.5)


# =======================================================
# 2. THE EFFICIENT FRONTIER (Spatial Metaphors over Numbers)
# =======================================================
class Vis_TheOptimalEdge(Scene):
    def construct(self):
        title = Text("2. The Optimal Edge (Markowitz)", font_size=32).to_corner(UL)
        self.add(title)

        insight = PhilosophyInsight(
            "Geometry of Risk",
            "We don't search numbers.\nWe search space. The chaotic\ncloud of portfolios hits a\nhard mathematical ceiling.\nThat ceiling is the frontier.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.5))

        axes = Axes(
            x_range=[0, 0.4, 0.1], y_range=[0, 0.25, 0.05], x_length=6, y_length=4.5
        ).to_edge(LEFT, buff=1)
        self.play(FadeIn(axes))

        np.random.seed(99)
        dots = VGroup()
        for i in range(300):
            vol = np.random.uniform(0.05, 0.35)
            max_r = 0.15 * np.sqrt((vol - 0.05) / 0.2) if vol > 0.05 else 0
            if max_r > 0:
                ret = np.random.uniform(0.01, max_r)
                dots.add(Dot(axes.c2p(vol, ret), color=COLOR_MUTED, radius=0.03))

        # Rhythm: Raindrop effect for chaos
        self.play(
            LaggedStart(*[FadeIn(d, shift=DOWN * 0.1) for d in dots], lag_ratio=0.005), run_time=2
        )

        # The transformation: Pulling out the frontier
        frontier = axes.plot(
            lambda x: 0.15 * np.sqrt((x - 0.05) / 0.2), x_range=[0.05, 0.35], color=COLOR_WHITE
        )
        glow = axes.plot(
            lambda x: 0.15 * np.sqrt((x - 0.05) / 0.2), x_range=[0.05, 0.35], color=COLOR_POSITIVE
        ).set_stroke(width=12, opacity=0.3)

        self.play(
            Create(frontier), FadeIn(glow), run_time=1.5, rate_func=rate_functions.ease_out_expo
        )

        # Color shifting: The dots near the edge turn green (meaning = optimal)
        optimal_anims = []
        for d in dots:
            coords = axes.p2c(d.get_center())
            vol_x = coords[0]
            ret_y = coords[1]
            max_y = 0.15 * np.sqrt((vol_x - 0.05) / 0.2)
            if max_y - ret_y < 0.015:
                optimal_anims.append(d.animate.set_color(COLOR_POSITIVE).scale(1.5))

        self.play(*optimal_anims, run_time=1)
        self.wait(1.5)


# =======================================================
# 3. REGIME CHANGE & STRESS (Color Shifts = Deep Semantics)
# =======================================================
class Vis_RegimePhaseShift(Scene):
    def construct(self):
        title = Text("3. Phase Shifts & Stress", font_size=32).to_corner(UL)
        self.add(title)
        self.camera.background_color = COLOR_BG

        insight = PhilosophyInsight(
            "Regime Collapse",
            "The market is not a line, it's a state.\nWhen a crisis hits (x=5), the literal\nphysics of the environment shatter.\nCorrelations go to 1, math goes red.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.5))

        axes = Axes(x_range=[0, 10, 2], y_range=[0, 200, 50], x_length=6, y_length=4.5).to_edge(
            LEFT, buff=1
        )
        self.play(Create(axes))

        # Phase 1: Normal State (Blue/Green)
        x_vals_1 = np.linspace(0, 5, 100)
        y_vals_1 = 100 + x_vals_1 * 5 + np.sin(x_vals_1 * 4) * 10
        normal_graph = axes.plot_line_graph(
            x_vals_1, y_vals_1, add_vertex_dots=False, line_color=COLOR_BLUE
        )

        self.play(Create(normal_graph), run_time=2, rate_func=linear)

        # The Pivot: The exact moment of the crisis.
        # Motion implies state change: The background pulses, the grid turns red.
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

        # Phase 2: Collapse (Red, volatile, jagged)
        x_vals_2 = np.linspace(5, 10, 100)
        np.random.seed(1)
        y_vals_2 = y_vals_1[-1] - (x_vals_2 - 5) * 20 + np.random.normal(0, 15, 100)
        crash_graph = axes.plot_line_graph(
            x_vals_2, y_vals_2, add_vertex_dots=False, line_color=COLOR_NEGATIVE
        ).set_stroke(width=2)

        # Notice we animate this differently: violent bursts instead of smooth linear
        self.play(Create(crash_graph), run_time=1.5, rate_func=rate_functions.wiggle)

        # BWC Alpha: BWC Survives the regime shift
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


# =======================================================
# 4. DATA PIPELINE (Abstraction & Architecture)
# =======================================================
class Vis_StructuralDataFlow(Scene):
    def construct(self):
        title = Text("4. The BWC Pipeline Logic", font_size=32).to_corner(UL)
        self.add(title)

        insight = PhilosophyInsight(
            "Taming Entropy",
            "The web is chaotic entropy.\nDuckDB isn't just storage;\nit is a structural lattice that\nforces chaos into strict,\ncomputable vectors.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.5))

        # Entropy: Scattered data particles from Spiders
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

        # Structure: The DuckDB array
        db_frame = Rectangle(
            width=2, height=3, stroke_color=COLOR_BLUE, fill_color=COLOR_BLUE, fill_opacity=0.1
        ).move_to(LEFT * 1 + UP * 1)
        lbl = Text("DuckDB Tensor", font_size=18, color=COLOR_BLUE).next_to(db_frame, DOWN)
        self.play(Create(db_frame), FadeIn(lbl))

        # The Transformation: Particles lose entropy and snap into perfect structural grids
        grid_spots = []
        for r in range(8):
            for c in range(5):
                grid_spots.append(
                    db_frame.get_corner(UL) + RIGHT * (0.2 + c * 0.4) + DOWN * (0.2 + r * 0.38)
                )

        snap_anims = []
        for i, dot in enumerate(chaos_dots):
            # Change color to signify it is now computational data
            target_dot = Dot(grid_spots[i], color=COLOR_POSITIVE, radius=0.06)
            snap_anims.append(Transform(dot, target_dot))

        # Rhythm: Slow build, sudden snap
        self.wait(0.5)
        self.play(*snap_anims, run_time=1.2, rate_func=rate_functions.ease_in_out_back)

        # Flow into the Agent Model
        model = (
            Polygon(UP * 0.5, LEFT * 0.5, RIGHT * 0.5, color=COLOR_ACCENT, fill_opacity=0.3)
            .scale(1.5)
            .move_to(RIGHT * 3 + UP * 1)
        )
        model.rotate(-PI / 2)
        m_lbl = Text("Fusion Agent", font_size=16, color=COLOR_ACCENT).next_to(model, DOWN)
        self.play(FadeIn(model, scale=0.8), FadeIn(m_lbl))

        # The structure moves holistically
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


# =======================================================
# 5. RISK ALLOCATION SCALE (Balancing Invariants)
# =======================================================
class Vis_InvariantBalancing(Scene):
    def construct(self):
        title = Text("5. The Optimization Invariant", font_size=32).to_corner(UL)
        self.add(title)

        insight = PhilosophyInsight(
            "Dynamic Equilibrium",
            "A portfolio is physical.\nIf tech volatility spikes,\nthe weight on the scale\ngets heavier. Cash must\ncounter-balance to survive.",
        )
        self.play(FadeIn(insight, shift=LEFT * 0.5))

        # A perfect scale representing the Agent's optimizer
        beam = Line(LEFT * 2.5, RIGHT * 2.5, color=COLOR_WHITE, stroke_width=6).move_to(
            LEFT * 1 + UP * 1
        )
        fulcrum = Polygon(
            UP * 0, LEFT * 0.5, RIGHT * 0.5, color=COLOR_MUTED, fill_opacity=1
        ).next_to(beam, DOWN, buff=0)

        self.play(Create(beam), FadeIn(fulcrum))

        # Left side: Tech (Volatile), Right side: Cash (Stable)
        tech_box = Square(side_length=1, color=COLOR_PURPLE, fill_opacity=0.8).next_to(
            beam.get_left(), UP, buff=0
        )
        tech_lbl = Text("Tech", font_size=16).move_to(tech_box.get_center())

        cash_box = Rectangle(width=1, height=1, color=COLOR_POSITIVE, fill_opacity=0.8).next_to(
            beam.get_right(), UP, buff=0
        )
        cash_lbl = Text("Cash", font_size=16).move_to(cash_box.get_center())

        self.play(FadeIn(tech_box), FadeIn(tech_lbl), FadeIn(cash_box), FadeIn(cash_lbl))

        # The transformation: Volatility spikes! The Tech box physically grows, and thus heavier.
        vol_spike = Text("Vol = 0.45", font_size=18, color=COLOR_NEGATIVE).next_to(tech_box, UP)
        self.play(
            Write(vol_spike),
            tech_box.animate.scale(1.5, about_edge=DOWN).set_color(COLOR_NEGATIVE),
            run_time=1,
        )

        # Visual Intuition: the beam tilts due to the invisible physics of risk
        self.play(
            Rotate(beam, angle=0.2, about_point=fulcrum.get_top()),
            tech_box.animate.shift(DOWN * 0.4 + RIGHT * 0.1),
            tech_lbl.animate.shift(DOWN * 0.4 + RIGHT * 0.1),
            vol_spike.animate.shift(DOWN * 0.4 + RIGHT * 0.1),
            cash_box.animate.shift(UP * 0.4 + RIGHT * 0.1),
            cash_lbl.animate.shift(UP * 0.4 + RIGHT * 0.1),
            run_time=1,
            rate_func=rate_functions.ease_in_out_sine,
        )

        # The Agent Optimization: To restore parity, we shrink the tech allocation size (dollar size)
        shrink_txt = Text("optimizer.py -> Cut Exposure", font_size=18, color=COLOR_ACCENT).next_to(
            fulcrum, DOWN, buff=1
        )
        self.play(Write(shrink_txt))

        # Tech physically shrinks its dollar block to restore balance
        self.play(
            tech_box.animate.scale(0.5, about_edge=DOWN).set_color(COLOR_PURPLE),
            Rotate(beam, angle=-0.2, about_point=fulcrum.get_top()),
            tech_lbl.animate.shift(UP * 0.4 + LEFT * 0.1),
            vol_spike.animate.shift(UP * 0.4 + LEFT * 0.1),
            cash_box.animate.shift(DOWN * 0.4 + LEFT * 0.1),
            cash_lbl.animate.shift(DOWN * 0.4 + LEFT * 0.1),
            run_time=1.5,
            rate_func=rate_functions.ease_out_elastic,
        )

        self.wait(1.5)
