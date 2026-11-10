import json
from manim import *

# Configure dark tech theme globally
config.background_color = "#0F0F14"
config.pixel_width = 1280
config.pixel_height = 720
config.frame_rate = 30

class TechExplainerScene(Scene):
    def construct(self):
        # 1. Load the JSON data (which can be modified by your text input or local LLM)
        try:
            with open("animation_config.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {
                "topic": "Python Code Animation",
                "steps": [{"title": "Default", "code": "print('Hello World')", "highlight": "print"}]
            }

        # 2. Title Header Animation
        title = Text(data["topic"], font_size=40, color=BLUE_D).to_edge(UP, buff=0.8)
        underline = Line(LEFT, RIGHT, color=GREEN_C).set_width(len(data["topic"]) * 0.3).next_to(title, DOWN)
        
        self.play(FadeIn(title, shift=DOWN), Create(underline), run_time=1)
        self.wait(0.5)

        # 3. Iterate through JSON steps and animate code/text programmatically
        previous_mob = underline
        
        for i, step in enumerate(data["steps"]):
            # Group box for each step
            step_title = Text(step["title"], font_size=28, color=WHITE).align_to(title, LEFT)
            code_block = Code(
                code=step["code"],
                language="python",
                theme="monokai",
                font_size=24
            ).scale(0.9)

            # Layout positioning
            v_group = VGroup(step_title, code_block).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
            v_group.move_to(ORIGIN)

            if i == 0:
                self.play(FadeIn(v_group, shift=UP), run_time=0.8)
            else:
                self.play(Transform(previous_mob, v_group), run_time=0.8)
            
            self.wait(1.5)
            previous_mob = v_group

        # 4. Outro
        outro = Text("Built 100% with Python Code", font_size=24, color=GRAY).to_edge(DOWN, buff=0.5)
        self.play(Write(outro), run_time=1)
        self.wait(2)
