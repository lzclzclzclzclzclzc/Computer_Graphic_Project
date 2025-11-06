# fill.py
from typing import Callable, Iterable, Tuple, List, Union

Color = Union[int, Tuple[int, int, int, int], Tuple[int, int, int]]
ReadFunc = Callable[[int, int], Color]  # 传入 (x,y) 返回当前像素颜色

def _col_equal(a: Color, b: Color, tol: int = 0) -> bool:
    if isinstance(a, int) and isinstance(b, int):
        return abs(a - b) <= tol
    if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
        return all(abs(int(a[i]) - int(b[i])) <= tol for i in range(len(a)))
    return False

def scanline_flood_fill(
    seed_x: int,
    seed_y: int,
    read: ReadFunc,          # 读取当前画布像素颜色
    width: int,
    height: int,
    new_color: Color,
    shape_id: str,
    pen_w: int = 1,
    connectivity: int = 4,   # 4 或 8 邻接
    tol: int = 0,            # 颜色匹配容差
) -> List[dict]:
    """
    泛洪填充：把和起点同色的连通区域全部替换为 new_color。
    返回像素点列表（和你的 rasterize 一致的结构）。
    不直接写画布；由上层统一渲染。
    """
    if not (0 <= seed_x < width and 0 <= seed_y < height):
        return []

    target = read(seed_x, seed_y)
    if _col_equal(target, new_color, tol):
        return []

    out: List[dict] = []
    visited = set()  # 防止重复入栈/扫描
    stack: List[Tuple[int, int]] = [(seed_x, seed_y)]

    def ok(x: int, y: int) -> bool:
        return 0 <= x < width and 0 <= y < height and ((x, y) not in visited) and _col_equal(read(x, y), target, tol)

    while stack:
        x, y = stack.pop()

        # 向左扩展
        xL = x
        while xL - 1 >= 0 and ok(xL - 1, y):
            xL -= 1

        # 向右扩展
        xR = x
        while xR + 1 < width and ok(xR + 1, y):
            xR += 1

        # 填充 [xL, xR]
        for xx in range(xL, xR + 1):
            visited.add((xx, y))
            out.append({"x": xx, "y": y, "color": new_color, "id": shape_id, "w": max(1, int(pen_w))})

        # 检查上一行 / 下一行的可扩张段作为新种子
        for ny in (y - 1, y + 1):
            if ny < 0 or ny >= height:
                continue
            xx = xL
            while xx <= xR:
                # 跳过不匹配或已访问的像素
                while xx <= xR and ((xx, ny) in visited or not _col_equal(read(xx, ny), target, tol)):
                    xx += 1
                if xx > xR:
                    break
                # 找到一个可扩张子区间 [sL..sR]
                sL = xx
                while xx <= xR and ((xx, ny) not in visited and _col_equal(read(xx, ny), target, tol)):
                    xx += 1
                sR = xx - 1
                # ★ 不要在这里标记 visited，让该行在弹栈时自行左右扩展
                # 为了稳妥，压入端点+中点（三者随便一个也行，三者最稳）
                mid = (sL + sR) // 2
                stack.append((sL, ny))
                stack.append((mid, ny))
                stack.append((sR, ny))

        # 8 邻接时，加两侧对角的探测（可选，代价很小）
        if connectivity == 8:
            for (sx, sy) in ((xL - 1, y - 1), (xL - 1, y + 1), (xR + 1, y - 1), (xR + 1, y + 1)):
                if 0 <= sx < width and 0 <= sy < height and ok(sx, sy):
                    stack.append((sx, sy))

    return out


def scanline_boundary_fill(
    seed_x: int,
    seed_y: int,
    read: ReadFunc,
    width: int,
    height: int,
    boundary_color: Color,
    new_color: Color,
    shape_id: str,
    pen_w: int = 1,
    tol: int = 0,
) -> List[dict]:
    """
    边界填充：遇到 boundary_color 停止。
    """
    def is_inside(x: int, y: int) -> bool:
        c = read(x, y)
        # 只要不是边界色，并且不是新颜色（避免反复）
        return (not _col_equal(c, boundary_color, tol)) and (not _col_equal(c, new_color, tol))

    if not (0 <= seed_x < width and 0 <= seed_y < height) or not is_inside(seed_x, seed_y):
        return []

    out: List[dict] = []
    visited = set()
    stack = [(seed_x, seed_y)]

    def ok(x: int, y: int) -> bool:
        return 0 <= x < width and 0 <= y < height and ((x, y) not in visited) and is_inside(x, y)

    while stack:
        x, y = stack.pop()

        xL = x
        while xL - 1 >= 0 and ok(xL - 1, y):
            xL -= 1
        xR = x
        while xR + 1 < width and ok(xR + 1, y):
            xR += 1

        for xx in range(xL, xR + 1):
            visited.add((xx, y))
            out.append({"x": xx, "y": y, "color": new_color, "id": shape_id, "w": max(1, int(pen_w))})

        for ny in (y - 1, y + 1):
            if ny < 0 or ny >= height:
                continue
            xx = xL
            while xx <= xR:
                while xx <= xR and ((xx, ny) in visited or not is_inside(xx, ny)):
                    xx += 1
                if xx > xR:
                    break
                sL = xx
                while xx <= xR and ((xx, ny) not in visited and is_inside(xx, ny)):
                    xx += 1
                sR = xx - 1
                mid = (sL + sR) // 2
                stack.append((sL, ny))
                stack.append((mid, ny))
                stack.append((sR, ny))

    return out