# backend/app/services/scene_service.py
from typing import Dict, List
from ..domain.scene import Scene
from ..domain.shapes import Line, Rectangle

class SceneService:
    def __init__(self, scene: Scene):
        self.scene = scene

    def add_line(self, d: Dict) -> List[Dict]:
        line = Line(int(d["x1"]), int(d["y1"]), int(d["x2"]), int(d["y2"]))
        self.scene.add(line)
        return self.scene.flatten_points()

    def add_rect(self, d: Dict) -> List[Dict]:
        rect = Rectangle(int(d["x1"]), int(d["y1"]), int(d["x2"]), int(d["y2"]))
        self.scene.add(rect)
        return self.scene.flatten_points()

    def undo(self) -> List[Dict]:
        self.scene.undo()
        return self.scene.flatten_points()

    def get_points(self) -> List[Dict]:
        return self.scene.flatten_points()