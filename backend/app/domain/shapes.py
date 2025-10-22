# backend/app/domain/shapes.py
from dataclasses import dataclass
from typing import List, Dict

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

# --- 加入 color 参数 ---
@dataclass
class Shape:
    color: str = "#ff0000"  # 默认红色
    def rasterize(self) -> List[Point]:
        raise NotImplementedError

@dataclass
class Line(Shape):
    x1: int = 0; y1: int = 0
    x2: int = 0; y2: int = 0
    def rasterize(self) -> List[Point]:
        pts = bresenham(self.x1, self.y1, self.x2, self.y2)
        return [{"x": p["x"], "y": p["y"], "color": self.color} for p in pts]

@dataclass
class Rectangle(Shape):
    x1: int = 0; y1: int = 0
    x2: int = 0; y2: int = 0
    def rasterize(self) -> List[Point]:
        x_min, x_max = sorted([self.x1, self.x2])
        y_min, y_max = sorted([self.y1, self.y2])
        edges = []
        edges += bresenham(x_min, y_min, x_max, y_min)
        edges += bresenham(x_min, y_max, x_max, y_max)
        edges += bresenham(x_min, y_min, x_min, y_max)
        edges += bresenham(x_max, y_min, x_max, y_max)
        return [{"x": p["x"], "y": p["y"], "color": self.color} for p in edges]