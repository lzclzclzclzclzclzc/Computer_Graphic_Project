# backend/app/services/scene_service.py
import re
from typing import Dict, List, Optional
from ..domain.scene import Scene
from ..domain.shapes import Line, Rectangle

HEX = re.compile(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")

def _pick_color(c: Optional[str], default: str = "#ff0000") -> str:
    if isinstance(c, str) and HEX.match(c):
        return c.lower()
    return default

class SceneService:
    def __init__(self, scene: Scene):
        self.scene = scene

    # 接收 color（由蓝图那边传入）
    def add_line(self, d: Dict, color: Optional[str] = None) -> List[Dict]:
        c = _pick_color(color)
        line = Line(
            x1=int(d["x1"]), y1=int(d["y1"]),
            x2=int(d["x2"]), y2=int(d["y2"]),
            color=c
        )
        self.scene.add(line)
        return self.scene.flatten_points()

    def add_rect(self, d: Dict, color: Optional[str] = None) -> List[Dict]:
        c = _pick_color(color)
        rect = Rectangle(
            x1=int(d["x1"]), y1=int(d["y1"]),
            x2=int(d["x2"]), y2=int(d["y2"]),
            color=c
        )
        self.scene.add(rect)
        return self.scene.flatten_points()

    def undo(self) -> List[Dict]:
        self.scene.undo()
        return self.scene.flatten_points()

    def get_points(self) -> List[Dict]:
        return self.scene.flatten_points()

    def move_shape(self, d: Dict) -> List[Dict]:
        sid = d.get("id")
        dx = int(d.get("dx", 0))
        dy = int(d.get("dy", 0))
        self.scene.move(sid, dx, dy)
        return self.scene.flatten_points()