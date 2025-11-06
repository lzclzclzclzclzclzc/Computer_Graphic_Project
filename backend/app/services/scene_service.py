# backend/app/services/scene_service.py

import re
from typing import Dict, List, Optional
from ..domain.scene import Scene
from ..domain.shapes import Line, Rectangle, Circle, Bezier, Polygon, BSpline,FillBlob
from ..domain.fill import scanline_flood_fill
from uuid import uuid4

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

def _hex_to_rgba(s: str):
    s = s.strip().lower()
    if s.startswith("#"): s = s[1:]
    if len(s) == 3:
        s = "".join([c*2 for c in s])
    r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16)
    return (r, g, b, 255)

def _to_rgba(c):
    if isinstance(c, str) and HEX.match(c): return _hex_to_rgba(c)
    if isinstance(c, (list, tuple)):
        if len(c) == 3: return (int(c[0]), int(c[1]), int(c[2]), 255)
        if len(c) == 4: return tuple(int(v) for v in c)
    if isinstance(c, int): return (c, c, c, 255)
    return (0, 0, 0, 255)

def _rgba_to_hex(c):
    if isinstance(c, str) and HEX.match(c): return c.lower()
    if isinstance(c, (list, tuple)) and len(c) >= 3:
        r, g, b = int(c[0]), int(c[1]), int(c[2])
        return f"#{r:02x}{g:02x}{b:02x}"
    if isinstance(c, int):
        return f"#{c:02x}{c:02x}{c:02x}"
    return "#000000"

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


    def bucket_fill(
            self,
            x: int,
            y: int,
            new_color,  # '#rrggbb' | (r,g,b[,a]) | int
            width: int,
            height: int,
            connectivity: int = 4,
            tol: int = 0,
            bg_color: str = "#ffffff",  # 画布背景色（没画到的像素）
    ) -> List[Dict]:
        """
        在 (x,y) 对与起点同色的区域做连通填充；把填充像素作为一个 FillBlob shape 加入场景。
        返回最新 flatten_points()。
        """
        # 1) 构建 read(x,y)：从当前场景的像素点映射出 RGBA
        rgba_bg = _to_rgba(bg_color)
        rgbamap = {}
        for p in self.scene.flatten_points():
            rgbamap[(int(p["x"]), int(p["y"]))] = _to_rgba(p["color"])

        def read(xx: int, yy: int):
            return rgbamap.get((xx, yy), rgba_bg)

        # 2) 算法产出像素（算法内部用 RGBA 对比）
        fill_id = f"fill-{uuid4().hex[:8]}"
        rgba_new = _to_rgba(new_color)
        raw_pts = scanline_flood_fill(
            seed_x=int(x), seed_y=int(y),
            read=read,
            width=int(width), height=int(height),
            new_color=rgba_new,
            shape_id=fill_id,
            pen_w=1, connectivity=int(connectivity), tol=int(tol)
        )

        if not raw_pts:
            return self.scene.flatten_points()

        # 3) 转回你场景的颜色格式（仍用 hex），打包成 FillBlob 形状
        hex_color = _rgba_to_hex(rgba_new)
        pixels = []
        for p in raw_pts:
            pixels.append({
                "x": p["x"],
                "y": p["y"],
                "color": hex_color,  # 存 hex，和你其他 shape 一致
                "id": fill_id,
                "w": 1
            })

        blob = FillBlob(pixels=pixels, color=hex_color, pen_width=1)
        self.scene.add(blob)

        return self.scene.flatten_points()

    # services/scene_service.py 里加：
    def bucket_fill_meta(
            self, x: int, y: int, new_color, width: int, height: int,
            connectivity: int = 4, tol: int = 0, bg_color: str = "#ffffff"
    ):
        # --- 基本逻辑与 bucket_fill 一致 ---
        rgba_bg = _to_rgba(bg_color)
        rgbamap = {}
        for p in self.scene.flatten_points():
            rgbamap[(int(p["x"]), int(p["y"]))] = _to_rgba(p["color"])

        def read(xx: int, yy: int):
            return rgbamap.get((xx, yy), rgba_bg)

        from uuid import uuid4
        fill_id = f"fill-{uuid4().hex[:8]}"
        rgba_new = _to_rgba(new_color)
        raw_pts = scanline_flood_fill(
            seed_x=int(x), seed_y=int(y), read=read,
            width=int(width), height=int(height),
            new_color=rgba_new, shape_id=fill_id,
            pen_w=1, connectivity=int(connectivity), tol=int(tol)
        )
        if not raw_pts:
            return {"points": self.scene.flatten_points(), "fill_id": None, "pixels": []}

        hex_color = _rgba_to_hex(rgba_new)
        pixels = [{"x": p["x"], "y": p["y"], "color": hex_color, "id": fill_id, "w": 1} for p in raw_pts]

        blob = FillBlob(pixels=pixels, color=hex_color, pen_width=1)
        self.scene.add(blob)

        return {"points": self.scene.flatten_points(), "fill_id": fill_id, "pixels": pixels}

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



