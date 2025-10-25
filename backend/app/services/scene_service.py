# backend/app/services/scene_service.py
import re
from typing import Dict, List, Optional
from ..domain.scene import Scene
from ..domain.shapes import Line, Rectangle, Circle, Bezier

HEX = re.compile(r"^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")

def _pick_color(c: Optional[str], default: str = "#ff0000") -> str:
    if isinstance(c, str) and HEX.match(c):
        return c.lower()
    return default

def _pick_width(w: Optional[int], fallback: int = 1) -> int:
    try:
        v = int(w) if w is not None else fallback
    except Exception:
        v = fallback
    return max(1, min(64, v))  # 简单限幅，避免异常值

class SceneService:
    def __init__(self, scene: Scene):
        self.scene = scene

    # 注意：多接一个 width（蓝图会传入），如果没传则从 d["width"] 兜底
    def add_line(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)
        line = Line(
            x1=int(d["x1"]), y1=int(d["y1"]),
            x2=int(d["x2"]), y2=int(d["y2"]),
            color=c,
            pen_width=w,             # <- 关键：把线宽传进图形
        )
        self.scene.add(line)
        return self.scene.flatten_points()

    def add_rect(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)
        rect = Rectangle(
            x1=int(d["x1"]), y1=int(d["y1"]),
            x2=int(d["x2"]), y2=int(d["y2"]),
            color=c,
            pen_width=w,             # <- 同理
        )
        self.scene.add(rect)
        return self.scene.flatten_points()

    def add_circle(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        """
        d 应包含 x1,y1,x2,y2,x3,y3 三个点；color 与 width 可选（由蓝图传入）
        """
        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)
        # 验证并构造 Circle 实例（Circle 类将在 domain.shapes.py 中添加）
        # Scene.add 将负责把 shape 放入场景
        circle = Circle(
            x1=int(d["x1"]), y1=int(d["y1"]),
            x2=int(d["x2"]), y2=int(d["y2"]),
            x3=int(d["x3"]), y3=int(d["y3"]),
            color=c,
            pen_width=w,
        )
        self.scene.add(circle)
        return self.scene.flatten_points()
    
    def add_bezier(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        
        pts = d.get("points", [])
        if not isinstance(pts, list) or len(pts) < 2:
            raise ValueError("Bezier 曲线至少需要两个控制点")

        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)

        bezier = Bezier(points=pts, color=c, pen_width=w)
        self.scene.add(bezier)
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
    
    def clear(self):
        self.scene.clear()
        return self.get_points()
    
    