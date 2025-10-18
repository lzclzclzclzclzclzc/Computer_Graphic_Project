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