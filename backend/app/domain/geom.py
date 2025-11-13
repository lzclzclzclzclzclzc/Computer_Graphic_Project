from dataclasses import dataclass
import math

@dataclass
class Mat2x3:
    a: float = 1; c: float = 0; tx: float = 0
    b: float = 0; d: float = 1; ty: float = 0

    def apply(self, x: float, y: float):
        """把矩阵作用在点 (x, y) 上"""
        nx = self.a * x + self.c * y + self.tx
        ny = self.b * x + self.d * y + self.ty
        return nx, ny

    def __matmul__(self, other: "Mat2x3") -> "Mat2x3":
        """矩阵乘法（右乘表示先执行）"""
        return Mat2x3(
            a = self.a*other.a + self.c*other.b,
            c = self.a*other.c + self.c*other.d,
            tx = self.a*other.tx + self.c*other.ty + self.tx,
            b = self.b*other.a + self.d*other.b,
            d = self.b*other.c + self.d*other.d,
            ty = self.b*other.tx + self.d*other.ty + self.ty,
        )

    @staticmethod
    def identity() -> "Mat2x3":
        return Mat2x3()

    @staticmethod
    def translation(dx: float, dy: float) -> "Mat2x3":
        return Mat2x3(1, 0, dx, 0, 1, dy)

    @staticmethod
    def rotation(theta_rad: float) -> "Mat2x3":
        c = math.cos(theta_rad)
        s = math.sin(theta_rad)
        return Mat2x3(c, -s, 0, s, c, 0)

    @staticmethod
    def scale(sx: float, sy: float) -> "Mat2x3":
        return Mat2x3(sx, 0, 0, 0, sy, 0)

def _clip_against_edge(points, inside_fn, intersect_fn):
    """Sutherland–Hodgman 的单边裁剪"""
    if not points:
        return []

    out = []
    prev = points[-1]
    prev_inside = inside_fn(prev)

    for curr in points:
        curr_inside = inside_fn(curr)
        if prev_inside and curr_inside:
            # S -> S
            out.append(curr)
        elif prev_inside and not curr_inside:
            # S -> O
            out.append(intersect_fn(prev, curr))
        elif (not prev_inside) and curr_inside:
            # O -> S
            out.append(intersect_fn(prev, curr))
            out.append(curr)
        # O -> O 什么都不加
        prev, prev_inside = curr, curr_inside

    return out

def clip_polygon_rect(points, x_min, y_min, x_max, y_max):
    """
    points: [{'x': float, 'y': float}, ...]  世界坐标
    return: 裁完后的点，仍然按顺时针/逆时针闭合
    """

    # 依次对 left, right, bottom, top 裁
    # left: x >= x_min
    def inside_left(p): return p["x"] >= x_min
    def intersect_left(p1, p2):
        dx = p2["x"] - p1["x"]
        if dx == 0:
            return {"x": x_min, "y": p1["y"]}
        t = (x_min - p1["x"]) / dx
        return {"x": x_min, "y": p1["y"] + t * (p2["y"] - p1["y"])}

    # right: x <= x_max
    def inside_right(p): return p["x"] <= x_max
    def intersect_right(p1, p2):
        dx = p2["x"] - p1["x"]
        if dx == 0:
            return {"x": x_max, "y": p1["y"]}
        t = (x_max - p1["x"]) / dx
        return {"x": x_max, "y": p1["y"] + t * (p2["y"] - p1["y"])}

    # bottom: y >= y_min
    def inside_bottom(p): return p["y"] >= y_min
    def intersect_bottom(p1, p2):
        dy = p2["y"] - p1["y"]
        if dy == 0:
            return {"x": p1["x"], "y": y_min}
        t = (y_min - p1["y"]) / dy
        return {"x": p1["x"] + t * (p2["x"] - p1["x"]), "y": y_min}

    # top: y <= y_max
    def inside_top(p): return p["y"] <= y_max
    def intersect_top(p1, p2):
        dy = p2["y"] - p1["y"]
        if dy == 0:
            return {"x": p1["x"], "y": y_max}
        t = (y_max - p1["y"]) / dy
        return {"x": p1["x"] + t * (p2["x"] - p1["x"]), "y": y_max}

    out = points
    out = _clip_against_edge(out, inside_left,   intersect_left)
    out = _clip_against_edge(out, inside_right,  intersect_right)
    out = _clip_against_edge(out, inside_bottom, intersect_bottom)
    out = _clip_against_edge(out, inside_top,    intersect_top)

    # 都被剪没了
    # 顺便把坐标 round 成 int，跟你 rasterize 的习惯对齐
    return [{"x": int(round(p["x"])), "y": int(round(p["y"]))} for p in out]