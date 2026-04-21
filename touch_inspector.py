from kivy.app import App
from ui.screens.main_screen import MainScreen
from kivy.core.window import Window
from kivy.clock import Clock
import sys

class TestApp(App):
    def build(self):
        self.sm = MainScreen()
        return self.sm

    def inspect_touch(self, window, touch):
        print("\n=== TOUCH DOWN at ===", touch.pos)
        def walk(widget, indent=""):
            if widget.collide_point(*touch.pos):
                print(f"{indent}[COLLIDE] {widget.__class__.__name__} pos={widget.pos} size={widget.size} {getattr(widget, 'text', '')}")
            else:
                pass
            for child in widget.children:
                walk(child, indent + "  ")
        walk(self.sm)

    def on_start(self):
        Window.bind(on_touch_down=self.inspect_touch)
        # We will simulate a touch EXACTLY AT the toggle_btn coordinates
        Clock.schedule_once(self.simulate, 0.5)

    def simulate(self, dt):
        btn = self.sm.filter_panel.toggle_btn
        cx, cy = btn.center_x, btn.center_y
        print(f"Simulating touch at {cx}, {cy}")
        from kivy.input.providers.mouse import MouseMotionEvent
        # Kivy 2.3 way to make a touch (the previous failed, we'll bypass and just test the hit via Python loop)
        for widget in reversed(Window.children):
            pass # Just manual inspection code via recursive collision

        print("Simulated finding hits:")
        def get_hits(widget):
            if not widget.collide_point(cx, cy): return
            print(f"HITS: {widget.__class__.__name__} {getattr(widget, 'text', '')}")
            for c in widget.children:
                get_hits(c)
        get_hits(self.sm)
        sys.exit(0)

if __name__ == '__main__':
    TestApp().run()
