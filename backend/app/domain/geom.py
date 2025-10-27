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