# backend/app/domain/shapes.py
from dataclasses import dataclass, field
from typing import List, Dict
import uuid

Point = Dict[str, int]

def bresenham(x1, y1, x2, y2) -> List[Point]:
    x, y, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    dx, dy = abs(x2 - x), abs(y2 - y)
    sx, sy = (1 if x < x2 else -1), (1 if y < y2 else -1)
    err = dx - dy
    pts: List[Point] = []
    while True:
        pts.append({"x": x, "y": y})
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return pts

# ---- 支持颜色 & 线宽，并提供通用 move() ----
@dataclass
class Shape:
    color: str = "#ff0000"                       # 颜色
    pen_width: int = 1                           # 线宽（像素）
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def rasterize(self) -> List[Point]:
        raise NotImplementedError

    # 统一的平移接口：具体图形各自实现或复用父类默认（若有需要）
    def move(self, dx: int, dy: int) -> None:
        """默认不做事，由子类覆盖。"""
        pass

# ---- 直线 ----
@dataclass
class Line(Shape):
    x1: int = 0; y1: int = 0
    x2: int = 0; y2: int = 0

    def move(self, dx: int, dy: int) -> None:
        self.x1 += int(dx); self.y1 += int(dy)
        self.x2 += int(dx); self.y2 += int(dy)

    def rasterize(self) -> List[Point]:
        pts = bresenham(self.x1, self.y1, self.x2, self.y2)
        w = max(1, int(self.pen_width))
        return [{"x": p["x"], "y": p["y"], "color": self.color, "id": self.id, "w": w} for p in pts]

# ---- 矩形（描边）----
@dataclass
class Rectangle(Shape):
    x1: int = 0; y1: int = 0
    x2: int = 0; y2: int = 0

    def move(self, dx: int, dy: int) -> None:
        self.x1 += int(dx); self.y1 += int(dy)
        self.x2 += int(dx); self.y2 += int(dy)

    def rasterize(self) -> List[Point]:
        x_min, x_max = sorted([self.x1, self.x2])
        y_min, y_max = sorted([self.y1, self.y2])
        edges = []
        edges += bresenham(x_min, y_min, x_max, y_min)
        edges += bresenham(x_min, y_max, x_max, y_max)
        edges += bresenham(x_min, y_min, x_min, y_max)
        edges += bresenham(x_max, y_min, x_max, y_max)
        w = max(1, int(self.pen_width))
        return [{"x": p["x"], "y": p["y"], "color": self.color, "id": self.id, "w": w} for p in edges]

@dataclass
class Circle(Shape):
    x1: int = 0; y1: int = 0
    x2: int = 0; y2: int = 0
    x3: int = 0; y3: int = 0

    def move(self, dx: int, dy: int) -> None:
        self.x1 += int(dx); self.y1 += int(dy)
        self.x2 += int(dx); self.y2 += int(dy)
        self.x3 += int(dx); self.y3 += int(dy)

    def _circumcenter_and_radius(self):
        x1, y1 = float(self.x1), float(self.y1)
        x2, y2 = float(self.x2), float(self.y2)
        x3, y3 = float(self.x3), float(self.y3)

        d = 2 * (x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
        if abs(d) < 1e-8:
            return None, None

        ux = ((x1**2 + y1**2)*(y2 - y3) + (x2**2 + y2**2)*(y3 - y1) + (x3**2 + y3**2)*(y1 - y2)) / d
        uy = ((x1**2 + y1**2)*(x3 - x2) + (x2**2 + y2**2)*(x1 - x3) + (x3**2 + y3**2)*(x2 - x1)) / d
        cx, cy = ux, uy
        r = ((cx - x1)**2 + (cy - y1)**2) ** 0.5
        return cx, cy, r

    def rasterize(self) -> List[Point]:
        circ = self._circumcenter_and_radius()
        if circ is None or circ[0] is None:
            from .shapes import bresenham  # safe import
            pts = bresenham(self.x1, self.y1, self.x2, self.y2)
            w = max(1, int(self.pen_width))
            return [{"x": p["x"], "y": p["y"], "color": self.color, "id": self.id, "w": w} for p in pts]

        cx, cy, r = circ
        import math
        n = max(16, min(2000, int(2 * math.pi * max(1.0, r))))  # 使弧长近似为 1 像素
        pts = []
        for i in range(n):
            theta = 2 * math.pi * (i / n)
            x = int(round(cx + r * math.cos(theta)))
            y = int(round(cy + r * math.sin(theta)))
            pts.append({"x": x, "y": y})
        uniq = []
        seen = set()
        for p in pts:
            key = (p["x"], p["y"])
            if key not in seen:
                seen.add(key)
                uniq.append({"x": p["x"], "y": p["y"], "color": self.color, "id": self.id, "w": max(1, int(self.pen_width))})
        return uniq

# ---- n阶 Bézier 曲线 ----
@dataclass
class Bezier(Shape):
    points: List[Point] = field(default_factory=list)

    def move(self, dx: int, dy: int) -> None:
        """整体平移控制点"""
        for p in self.points:
            p["x"] += int(dx)
            p["y"] += int(dy)

    def _de_casteljau(self, t: float) -> Point:
        """使用 De Casteljau 算法计算给定 t (0~1) 的点"""
        pts = [{"x": p["x"], "y": p["y"]} for p in self.points]
        n = len(pts)
        for r in range(1, n):  # r 表示层数
            for i in range(n - r):
                pts[i]["x"] = (1 - t) * pts[i]["x"] + t * pts[i + 1]["x"]
                pts[i]["y"] = (1 - t) * pts[i]["y"] + t * pts[i + 1]["y"]
        return {"x": int(round(pts[0]["x"])), "y": int(round(pts[0]["y"]))}

    def rasterize(self) -> List[Point]:
        """离散化 Bézier 曲线"""
        if len(self.points) < 2:
            return []

        n_samples = max(32, len(self.points) * 50)  # 采样精度
        pts = []
        for i in range(n_samples + 1):
            t = i / n_samples
            p = self._de_casteljau(t)
            pts.append(p)

        # 去重 + 附加绘制信息
        seen = set()
        uniq = []
        for p in pts:
            key = (p["x"], p["y"])
            if key not in seen:
                seen.add(key)
                uniq.append({
                    "x": p["x"],
                    "y": p["y"],
                    "color": self.color,
                    "id": self.id,
                    "w": max(1, int(self.pen_width))
                })
        return uniq

# ---- 任意多边形 ----
@dataclass
class Polygon(Shape):
    points: List[Point] = field(default_factory=list)

    def move(self, dx: int, dy: int) -> None:
        for p in self.points:
            p["x"] += int(dx)
            p["y"] += int(dy)

    def rasterize(self) -> List[Point]:
        if len(self.points) < 3:
            return []

        pts: List[Point] = []
        n = len(self.points)
        for i in range(n):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % n]  
            edge_pts = bresenham(p1["x"], p1["y"], p2["x"], p2["y"])
            pts.extend(edge_pts)

        seen = set()
        uniq = []
        w = max(1, int(self.pen_width))
        for p in pts:
            key = (p["x"], p["y"])
            if key not in seen:
                seen.add(key)
                uniq.append({
                    "x": p["x"],
                    "y": p["y"],
                    "color": self.color,
                    "id": self.id,
                    "w": w
                })
        return uniq
    
