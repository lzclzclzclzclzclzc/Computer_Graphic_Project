# backend/app/domain/shapes.py
import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import uuid

from backend.app.domain.geom import Mat2x3

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


@dataclass
class Shape:
    color: str = "#ff0000"
    pen_width: int = 1
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    transform: Mat2x3 = field(default_factory=Mat2x3.identity)

    # ---- 通用变换 ----
    def translate(self, dx: float, dy: float):
        self.transform = Mat2x3.translation(dx, dy) @ self.transform

    def rotate(self, theta: float, cx: float = 0.0, cy: float = 0.0):
        to_origin = Mat2x3.translation(-cx, -cy)
        rot = Mat2x3.rotation(theta)
        back = Mat2x3.translation(cx, cy)
        self.transform = (back @ rot @ to_origin) @ self.transform

    def scale(self, sx: float, sy: float, cx: float = 0.0, cy: float = 0.0):
        to_origin = Mat2x3.translation(-cx, -cy)
        sc = Mat2x3.scale(sx, sy)
        back = Mat2x3.translation(cx, cy)
        self.transform = (back @ sc @ to_origin) @ self.transform

    def move(self, dx: float, dy: float):
        self.translate(dx, dy)

    def rasterize(self) -> List[Point]:
        raise NotImplementedError

# ---- 直线 ----
@dataclass
class Line(Shape):
    x1: int = 0; y1: int = 0
    x2: int = 0; y2: int = 0

    def rasterize(self) -> List[Point]:
        X1, Y1 = self.transform.apply(self.x1, self.y1)
        X2, Y2 = self.transform.apply(self.x2, self.y2)
        pts = bresenham(int(round(X1)), int(round(Y1)),
                        int(round(X2)), int(round(Y2)))
        w = max(1, int(self.pen_width))
        return [{"x": p["x"], "y": p["y"], "color": self.color, "id": self.id, "w": w} for p in pts]

# ---- 矩形（描边）----
@dataclass
class Rectangle(Shape):
    x1: float = 0; y1: float = 0
    x2: float = 0; y2: float = 0

    def rasterize(self) -> List[Point]:
        x_min, x_max = sorted([self.x1, self.x2])
        y_min, y_max = sorted([self.y1, self.y2])
        corners = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]

        edges = []
        for i in range(4):
            (x1, y1) = corners[i]
            (x2, y2) = corners[(i+1) % 4]
            X1, Y1 = self.transform.apply(x1, y1)
            X2, Y2 = self.transform.apply(x2, y2)
            edges += bresenham(int(round(X1)), int(round(Y1)), int(round(X2)), int(round(Y2)))

        seen = set()
        w = max(1, int(self.pen_width))
        uniq = []
        for p in edges:
            key = (p["x"], p["y"])
            if key not in seen:
                seen.add(key)
                uniq.append({"x": p["x"], "y": p["y"], "color": self.color, "id": self.id, "w": w})
        return uniq

@dataclass
class Circle(Shape):
    # 三个点（局部坐标系里）
    x1: float = 0; y1: float = 0
    x2: float = 0; y2: float = 0
    x3: float = 0; y3: float = 0

    def _circumcenter_and_radius_local(self) -> Optional[Tuple[float, float, float]]:
        """
        在局部坐标里，算经过 (x1,y1),(x2,y2),(x3,y3) 的外接圆心 (cx,cy) 和半径 r
        若三点几乎共线，返回 None
        """
        x1, y1 = float(self.x1), float(self.y1)
        x2, y2 = float(self.x2), float(self.y2)
        x3, y3 = float(self.x3), float(self.y3)

        d = 2 * (x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
        if abs(d) < 1e-8:
            return None

        ux = ((x1**2 + y1**2)*(y2 - y3) +
              (x2**2 + y2**2)*(y3 - y1) +
              (x3**2 + y3**2)*(y1 - y2)) / d
        uy = ((x1**2 + y1**2)*(x3 - x2) +
              (x2**2 + y2**2)*(x1 - x3) +
              (x3**2 + y3**2)*(x2 - x1)) / d

        cx, cy = ux, uy
        r = math.sqrt((cx - x1)**2 + (cy - y1)**2)
        return cx, cy, r

    def rasterize(self) -> List[Point]:
        """
        思路：
        1. 在局部空间下找到圆心和半径
        2. 均匀采样圆周点 (局部坐标)
        3. 用 self.transform.apply() 把采样点丢到世界坐标
        4. 去重，返回像素点
        如果三点共线，fallback 成一条线段（和你原本逻辑一致）
        """
        circ = self._circumcenter_and_radius_local()
        if circ is None:
            # 共线或退化，按一条直线处理
            from .shapes import bresenham  # 如果 bresenham 跟这个类同文件，去掉这行 import
            X1, Y1 = self.transform.apply(self.x1, self.y1)
            X2, Y2 = self.transform.apply(self.x2, self.y2)
            pts = bresenham(int(round(X1)), int(round(Y1)),
                            int(round(X2)), int(round(Y2)))
            w = max(1, int(self.pen_width))
            return [{"x": p["x"], "y": p["y"],
                     "color": self.color, "id": self.id, "w": w} for p in pts]

        cx_local, cy_local, r_local = circ

        # 计算采样密度：尽量让相邻采样点接近1px（在局部半径上估）
        n = max(16, min(2000, int(2 * math.pi * max(1.0, r_local))))

        raw_pts_world = []
        for i in range(n):
            theta = 2 * math.pi * (i / n)
            px_local = cx_local + r_local * math.cos(theta)
            py_local = cy_local + r_local * math.sin(theta)

            Xw, Yw = self.transform.apply(px_local, py_local)
            raw_pts_world.append({
                "x": int(round(Xw)),
                "y": int(round(Yw)),
            })

        # 去重并加绘制属性
        seen = set()
        uniq = []
        w = max(1, int(self.pen_width))
        for p in raw_pts_world:
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
# ---- n阶 Bézier 曲线 ----
@dataclass
class Bezier(Shape):
    # 控制点列表（局部坐标）
    points: List[Dict[str, float]] = field(default_factory=list)

    def _de_casteljau_world(self, t: float, world_ctrl_pts: List[Dict[str, float]]) -> Point:
        """
        在“世界坐标下的控制点”上运行 De Casteljau。
        world_ctrl_pts: [{'x': Xw, 'y': Yw}, ...] 已经过 transform
        返回 int-rounded 的点
        """
        tmp = [{"x": p["x"], "y": p["y"]} for p in world_ctrl_pts]
        n = len(tmp)
        for r in range(1, n):
            for i in range(n - r):
                tmp[i]["x"] = (1 - t) * tmp[i]["x"] + t * tmp[i + 1]["x"]
                tmp[i]["y"] = (1 - t) * tmp[i]["y"] + t * tmp[i + 1]["y"]
        return {
            "x": int(round(tmp[0]["x"])),
            "y": int(round(tmp[0]["y"])),
        }

    def rasterize(self) -> List[Point]:
        """
        做法：
        1. 把本地控制点通过 transform 映射到世界坐标 → world_ctrl_pts
        2. 在世界坐标上跑 De Casteljau（仿射下是等价的）
        3. 坐标离散成像素，去重，上色
        """
        if len(self.points) < 2:
            return []

        # 1. 映射控制点到世界坐标
        world_ctrl_pts: List[Dict[str, float]] = []
        for p in self.points:
            Xw, Yw = self.transform.apply(p["x"], p["y"])
            world_ctrl_pts.append({"x": Xw, "y": Yw})

        # 2. 采样
        n_samples = max(32, len(self.points) * 50)
        raw_pts = []
        for i in range(n_samples + 1):
            t = i / n_samples
            pt = self._de_casteljau_world(t, world_ctrl_pts)
            raw_pts.append(pt)

        # 3. 去重 + 上色
        seen = set()
        uniq: List[Point] = []
        w = max(1, int(self.pen_width))
        for p in raw_pts:
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
# ---- 任意多边形 ----
@dataclass
class Polygon(Shape):
    points: List[Point] = field(default_factory=list)

    def rasterize(self) -> List[Point]:
        if len(self.points) < 3:
            return []
        world_pts = []
        for p in self.points:
            X, Y = self.transform.apply(p["x"], p["y"])
            world_pts.append({"x": X, "y": Y})

        edges = []
        n = len(world_pts)
        for i in range(n):
            p1, p2 = world_pts[i], world_pts[(i+1) % n]
            edges += bresenham(int(round(p1["x"])), int(round(p1["y"])),
                               int(round(p2["x"])), int(round(p2["y"])))

        seen = set()
        uniq = []
        w = max(1, int(self.pen_width))
        for p in edges:
            key = (p["x"], p["y"])
            if key not in seen:
                seen.add(key)
                uniq.append({"x": p["x"], "y": p["y"], "color": self.color, "id": self.id, "w": w})
        return uniq