
from manim import *
import numpy as np

class ScatterToNetwork(Scene):
    def construct(self):
        title = Text("The Illusion of Diversification", font_size=36)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))

        nodes = [Dot(point=np.array([np.random.uniform(-4, 4), np.random.uniform(-2, 2), 0]), radius=0.15) for _ in range(27)]
        labels = [Text(f"A{i}", font_size=12).next_to(nodes[i], UP, buff=0.1) for i in range(27)]
        
        for n, l in zip(nodes, labels):
            self.play(FadeIn(n), FadeIn(l), run_time=0.1)
            
        self.wait(1)
        
        # Draw thick correlation lines
        lines = []
        for i in range(10):
            source = np.random.choice(nodes)
            target = np.random.choice(nodes)
            line = Line(source.get_center(), target.get_center(), stroke_width=4, color=YELLOW)
            lines.append(line)
            
        self.play(*[Create(l) for l in lines], run_time=2)
        self.wait(2)
        
        self.play(*[FadeOut(m) for m in self.mobjects])

class KruskalSequence(Scene):
    def construct(self):
        title = Text("The Prune: Minimum Spanning Tree", font_size=36)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        
        nodes = [Dot(point=np.array([np.random.uniform(-4, 4), np.random.uniform(-2, 2), 0]), radius=0.15) for _ in range(15)]
        
        lines = []
        for i in range(20):
            source = np.random.choice(nodes)
            target = np.random.choice(nodes)
            line = Line(source.get_center(), target.get_center(), stroke_width=2, color=GRAY)
            lines.append(line)
            
        self.add(*nodes, *lines)
        self.wait(1)
        
        # Fade out weak
        self.play(*[FadeOut(l) for l in lines[:10]], run_time=2)
        self.wait(1)
        
        # Highlight MST
        self.play(*[l.animate.set_color(GREEN).set_stroke(width=4) for l in lines[10:]])
        self.wait(2)
        
        self.play(*[FadeOut(m) for m in self.mobjects])

class NodeResizer(Scene):
    def construct(self):
        title = Text("Hierarchical Risk Parity Sizing", font_size=36)
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))

        nodes = [Dot(point=np.array([i - 3, 0, 0]), radius=0.2, color=BLUE) for i in range(7)]
        self.play(*[FadeIn(n) for n in nodes])
        
        self.wait(1)
        
        # Pulse and resize
        animations = []
        for i, n in enumerate(nodes):
            new_r = 0.1 + (i % 3) * 0.15
            animations.append(n.animate.scale(new_r / 0.2).set_color(RED if new_r > 0.3 else BLUE))
            
        self.play(*animations, run_time=2)
        self.wait(2)

