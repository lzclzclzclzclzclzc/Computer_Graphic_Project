# backend/app/services/scene_service.py

import re
from typing import Dict, List, Optional
from ..domain.scene import Scene
from ..domain.shapes import Line, Rectangle, Circle, Bezier, Polygon, BSpline, Arc

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
    # 限一下线宽，避免离谱输入
    return max(1, min(64, v))


class SceneService:
    def __init__(self, scene: Scene):
        self.scene = scene

    # -------------------------
    # 创建各种图形
    # -------------------------
    def add_line(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        """
        期望 d 里有: x1,y1,x2,y2
        """
        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)

        line = Line(
            x1=int(d["x1"]), y1=int(d["y1"]),
            x2=int(d["x2"]), y2=int(d["y2"]),
            color=c,
            pen_width=w,
        )
        self.scene.add(line)
        return self.scene.flatten_points()

    def add_rect(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        """
        期望 d 里有: x1,y1,x2,y2  视为对角点
        """
        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)

        rect = Rectangle(
            x1=int(d["x1"]), y1=int(d["y1"]),
            x2=int(d["x2"]), y2=int(d["y2"]),
            color=c,
            pen_width=w,
        )
        self.scene.add(rect)
        return self.scene.flatten_points()

    def add_circle(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        """
        期望 d 里有: x1,y1,x2,y2,x3,y3
        （用三点拟合外接圆）
        """
        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)

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
        """
        期望 d["points"] 是 [{x:..., y:...}, ...]
        """
        pts = d.get("points", [])
        if not isinstance(pts, list) or len(pts) < 2:
            raise ValueError("Bezier requires at least 2 points.")

        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)

        bezier = Bezier(points=pts, color=c, pen_width=w)
        self.scene.add(bezier)
        return self.scene.flatten_points()

    def add_polygon(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        """
        期望 d["points"] 是 [{x:..., y:...}, ...] 且至少3点
        """
        pts = d.get("points", [])
        if not isinstance(pts, list) or len(pts) < 3:
            raise ValueError("Polygon requires at least 3 points.")

        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)

        polygon = Polygon(points=pts, color=c, pen_width=w)
        self.scene.add(polygon)
        return self.scene.flatten_points()
    
    def add_bspline(
        self,
        d: Dict,
        degree: Optional[int] = None,
        color: Optional[str] = None,
        width: Optional[int] = None
    ) -> List[Dict]:
        """
        期望 d 包含:
        {
            "points": [{x:..., y:...}, ...],
            "degree": n   # 可选，默认为3
        }
        """
        pts = d.get("points", [])
        if not isinstance(pts, list) or len(pts) < 2:
            raise ValueError("B-Spline requires at least 2 control points.")

        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)

        bspline = BSpline(points=pts, order = degree + 1, color=c, pen_width=w)
        self.scene.add(bspline)

        return self.scene.flatten_points()


    def add_arc(self, d: Dict, color: Optional[str] = None, width: Optional[int] = None) -> List[Dict]:
        c = _pick_color(color)
        w = _pick_width(width if width is not None else d.get("width"), 1)

        arc = Arc(
            x1=int(d["x1"]), y1=int(d["y1"]),
            x2=int(d["x2"]), y2=int(d["y2"]),
            x3=int(d["x3"]), y3=int(d["y3"]),
            color=c,
            pen_width=w,
        )
        self.scene.add(arc)
        return self.scene.flatten_points()
    
    # -------------------------
    # 状态 / 绘制
    # -------------------------
    def get_points(self) -> List[Dict]:
        """
        展场景，返回像素点（前端画布用）
        """
        return self.scene.flatten_points()

    def dump_scene_state(self) -> Dict:
        """
        返回整个场景的结构化信息（每个 shape 的几何定义 + 当前 transform 矩阵）
        用于调试 / 前端显示控制框 / 保存工程
        """
        return self.scene.dump_scene_state()

    # -------------------------
    # 变换
    # -------------------------
    def translate_shape(self, shape_id: str, dx: float, dy: float) -> List[Dict]:
        pts = self.scene.translate_and_raster(shape_id, dx, dy)
        return pts

    def rotate_shape(self, shape_id: str, theta: float, cx: float, cy: float) -> bool:
        """
        绕 (cx, cy) 旋转指定图形 theta (弧度)。
        """
        return self.scene.rotate_shape(shape_id, theta, cx, cy)

    def scale_shape(self, shape_id: str, sx: float, sy: float, cx: float, cy: float) -> bool:
        """
        围绕 (cx, cy) 按 (sx, sy) 缩放指定图形。
        """
        return self.scene.scale_shape(shape_id, sx, sy, cx, cy)

    # -------------------------
    # undo / clear
    # -------------------------
    def undo(self) -> List[Dict]:
        self.scene.undo()
        return self.scene.flatten_points()

    def clear(self) -> List[Dict]:
        self.scene.clear()
        return self.scene.flatten_points()

    def begin_transform_session(self):
        self.scene.begin_batch()

    def end_transform_session(self):
        self.scene.end_batch()

    def clip_rect(self, shape_id, x1, y1, x2, y2):
        return self.scene.clip_shape_by_rect_and_raster(shape_id, x1, y1, x2, y2)



