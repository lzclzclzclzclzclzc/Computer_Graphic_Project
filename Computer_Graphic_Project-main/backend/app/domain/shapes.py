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

class Shape:
    def rasterize(self) -> List[Point]:
        raise NotImplementedError

@dataclass
class Line(Shape):
    x1: int; y1: int; x2: int; y2: int
    def rasterize(self) -> List[Point]:
        return bresenham(self.x1, self.y1, self.x2, self.y2)

@dataclass
class Rectangle(Shape):
    x1: int; y1: int; x2: int; y2: int
    def rasterize(self) -> List[Point]:
        top    = bresenham(self.x1, self.y1, self.x2, self.y1)
        right  = bresenham(self.x2, self.y1, self.x2, self.y2)
        bottom = bresenham(self.x2, self.y2, self.x1, self.y2)
        left   = bresenham(self.x1, self.y2, self.x1, self.y1)
        return top + right + bottom + left

from math import sqrt

@dataclass
class Circle(Shape):
    x1: int; y1: int
    x2: int; y2: int
    x3: int; y3: int

    def rasterize(self) -> List[Point]:
        # 计算圆心 (h, k) 和半径 r
        x1, y1, x2, y2, x3, y3 = self.x1, self.y1, self.x2, self.y2, self.x3, self.y3
        d = 2 * (x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
        if d == 0:
            return []  # 三点共线无法成圆
        h = ((x1**2 + y1**2)*(y2 - y3) + (x2**2 + y2**2)*(y3 - y1) + (x3**2 + y3**2)*(y1 - y2)) / d
        k = ((x1**2 + y1**2)*(x3 - x2) + (x2**2 + y2**2)*(x1 - x3) + (x3**2 + y3**2)*(x2 - x1)) / d
        r = sqrt((x1 - h)**2 + (y1 - k)**2)

        pts: List[Point] = []
        x, y = 0, int(round(r))
        d = 3 - 2 * r

        def add_points(cx, cy, x, y):
            pts.extend([
                {"x": int(round(cx + x)), "y": int(round(cy + y))},
                {"x": int(round(cx - x)), "y": int(round(cy + y))},
                {"x": int(round(cx + x)), "y": int(round(cy - y))},
                {"x": int(round(cx - x)), "y": int(round(cy - y))},
                {"x": int(round(cx + y)), "y": int(round(cy + x))},
                {"x": int(round(cx - y)), "y": int(round(cy + x))},
                {"x": int(round(cx + y)), "y": int(round(cy - x))},
                {"x": int(round(cx - y)), "y": int(round(cy - x))}
            ])

        while y >= x:
            add_points(h, k, x, y)
            x += 1
            if d > 0:
                y -= 1
                d = d + 4*(x - y) + 10
            else:
                d = d + 4*x + 6
        return pts
