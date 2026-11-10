import json
from manim import *

# Configure clean dark tech theme globally
config.background_color = "#0F0F14"
config.pixel_width = 1280
config.pixel_height = 720
config.frame_rate = 30

class TechExplainerScene(Scene):
    def construct(self):
        # 1. Load the JSON data directly (No AI / No LLM needed)
        try:
            with open("animation_config.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {
                "topic": "Locloud App",
                "steps": [{"title": "Error", "code": "print('Config not found')"}]
            }

        # 2. Animate Title Header
        title = Text(data["topic"], font_size=36, color=BLUE_D).to_edge(UP, buff=0.6)
        underline = Line(LEFT, RIGHT, color=GREEN_C).set_width(len(data["topic"]) * 0.25).next_to(title, DOWN, buff=0.2)
        
        self.play(FadeIn(title, shift=DOWN), Create(underline), run_time=0.8)
        self.wait(0.3)

        # 3. Iterate through JSON steps with clean fade transitions (No Overlap)
        current_step_group = None
        
        for i, step in enumerate(data["steps"]):
            # Step Title
            step_title = Text(step["title"], font_size=26, color=YELLOW_C)
            
            # Code / Description text box
            code_text = Text(
                step["code"], 
                font="Consolas", 
                font_size=20, 
                color=WHITE
            )
            
            # Background panel for code look
            box = SurroundingRectangle(code_text, color=BLUE_E, fill_color=BLACK, fill_opacity=0.85, buff=0.3, corner_radius=0.1)
            code_group = VGroup(box, code_text)

            # Group layout positioning
            v_group = VGroup(step_title, code_group).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
            v_group.move_to(ORIGIN)

            if i == 0:
                # Fade in the first step
                self.play(FadeIn(v_group, shift=UP), run_time=0.6)
            else:
                # Fade out previous step completely before bringing in the new one
                self.play(FadeOut(current_step_group, shift=DOWN), run_time=0.4)
                self.play(FadeIn(v_group, shift=UP), run_time=0.6)
            
            current_step_group = v_group
            self.wait(1.5)

        # Clean up the last step before outro
        if current_step_group:
            self.play(FadeOut(current_step_group), run_time=0.4)

        # 4. Outro signature
        outro = Text("Rendered 100% via Python Code & JSON (No AI)", font_size=18, color=GRAY).to_edge(DOWN, buff=0.4)
        self.play(Write(outro), run_time=0.8)
        self.wait(1.5)
