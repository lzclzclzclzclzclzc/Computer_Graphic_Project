# backend/app/domain/scene.py

from typing import List, Dict, Optional
import copy

from .shapes import Shape  # 假设你的 Line / Rectangle / Circle / Bezier / Polygon 都继承了 Shape

Point = Dict[str, int]


class Scene:
    def __init__(self):
        # 场景里的所有对象
        # 这里我改成 dict[str, Shape] 更稳：通过 id 直接索引，不用每次 for s in _shapes 找
        self._shapes: Dict[str, Shape] = {}

        # 撤销 / 重做栈。我们直接存快照（_shapes 的深拷贝）。
        self._undo: List[Dict[str, Shape]] = []
        self._redo: List[Dict[str, Shape]] = []
        self._batch_active: bool = False  # 是否处于一次连续操作中

    # ----------------------
    # 内部：拍快照给 undo
    # ----------------------
    def _snapshot_for_undo(self):
        # 注意：要 deepcopy 整个 dict，不然引用会串
        self._undo.append(copy.deepcopy(self._shapes))

    # ----------------------
    # 公共：场景管理
    # ----------------------
    def add(self, shape: Shape) -> str:
        """
        往场景里放一个新的 shape。
        返回它的 id，方便前端保存。
        """
        self._snapshot_for_undo()
        self._shapes[shape.id] = shape
        self._redo.clear()
        return shape.id

    def remove(self, shape_id: str) -> bool:
        """
        从场景里删一个对象。
        """
        if shape_id not in self._shapes:
            return False
        self._snapshot_for_undo()
        del self._shapes[shape_id]
        self._redo.clear()
        return True

    def clear(self):
        """
        清空场景。
        """
        if not self._shapes:
            return
        self._snapshot_for_undo()
        self._shapes.clear()
        self._redo.clear()

    def get_shape(self, shape_id: str) -> Optional[Shape]:
        """
        拿到 shape 引用，外部也可以自己玩。
        """
        return self._shapes.get(shape_id)

    # ----------------------
    # 撤销 / 重做
    # ----------------------
    def undo(self):
        if not self._undo:
            return
        # 当前状态推到 redo 栈
        self._redo.append(copy.deepcopy(self._shapes))
        # 取出上一个状态作为当前
        self._shapes = self._undo.pop()

    def redo(self):
        if not self._redo:
            return
        # 当前状态推回 undo 栈
        self._undo.append(copy.deepcopy(self._shapes))
        # 取出 redo 栈顶部为当前
        self._shapes = self._redo.pop()

    # ----------------------
    # 渲染（给前端画）
    # ----------------------
    def flatten_points(self) -> List[Point]:
        """
        把场景里所有 shape 的像素点合到一个数组里。
        你的前端画布目前正是吃这种结构，所以这个接口我保持不变。
        """
        pts: List[Point] = []
        for s in self._shapes.values():
            pts.extend(s.rasterize())
        return pts

    # ----------------------
    # 变换接口（核心升级）
    # ----------------------
    def translate_shape(self, sid: str, dx: float, dy: float) -> bool:
        if not sid or (dx == 0 and dy == 0):
            return False

        shp = self._shapes.get(sid)
        if shp is None:
            return False

        # 只有当不在 batch 状态时，才自动 snapshot。
        # 在拖拽批次中，begin_batch() 会提前拍一次。
        if not self._batch_active:
            self._snapshot_for_undo()
            self._redo.clear()

        # 真正改坐标
        if hasattr(shp, "translate"):
            shp.translate(dx, dy)
        else:
            # fallback：直接改它的坐标属性
            for attr in dir(shp):
                if attr.startswith("x") and isinstance(getattr(shp, attr), (int, float)):
                    setattr(shp, attr, getattr(shp, attr) + dx)
                elif attr.startswith("y") and isinstance(getattr(shp, attr), (int, float)):
                    setattr(shp, attr, getattr(shp, attr) + dy)

        return True

    def rotate_shape(self, shape_id: str, theta_rad: float, cx: float, cy: float) -> bool:
        """
        绕 (cx, cy) 旋转某个 shape。
        这个 (cx, cy) 应该来自前端，比如你前端的 center_point。
        """
        if shape_id not in self._shapes:
            return False
        if theta_rad == 0:
            return False

        self._snapshot_for_undo()

        shp = self._shapes[shape_id]
        shp.rotate(theta_rad, cx, cy)

        self._redo.clear()
        return True

    def scale_shape(self, shape_id: str, sx: float, sy: float, cx: float, cy: float) -> bool:
        """
        围绕 (cx, cy) 做缩放。
        sx, sy 是缩放倍数，比如 1.2 / 0.8 这种。
        就是你前端算出来的 scaleX, scaleY。
        """
        if shape_id not in self._shapes:
            return False
        # 如果缩放是 1,1 基本等于没缩
        if sx == 1 and sy == 1:
            return False

        self._snapshot_for_undo()

        shp = self._shapes[shape_id]
        shp.scale(sx, sy, cx, cy)

        self._redo.clear()
        return True

    # ----------------------
    # (可选) 导出当前场景状态，给前端/存档/调试
    # ----------------------
    def dump_scene_state(self) -> dict:
        """
        这个方法不是绘图，而是状态同步/调试用。
        - geometry: 图形的原始定义点（局部坐标）
        - transform: 目前累计的仿射矩阵
        前端如果想显示边框/控制柄，可以用这个信息自己算。
        """
        data = {
            "shapes": [],
        }
        for shp in self._shapes.values():
            # geometry: 我们不要去硬编码 shape 的字段名，
            #           还是动态读，这样 Circle / Polygon / Line 都能用。
            geometry_fields = {}
            for attr in dir(shp):
                if attr.startswith("_"):
                    continue
                if attr in ("color", "pen_width", "id", "transform",
                            "translate", "rotate", "scale",
                            "move", "rasterize"):
                    continue
                val = getattr(shp, attr)
                # 跳过可调用成员
                if callable(val):
                    continue
                geometry_fields[attr] = val

            data["shapes"].append({
                "id": shp.id,
                "type": shp.__class__.__name__,
                "color": shp.color,
                "pen_width": shp.pen_width,
                "geometry": geometry_fields,
                "transform": {
                    "a": shp.transform.a,
                    "c": shp.transform.c,
                    "tx": shp.transform.tx,
                    "b": shp.transform.b,
                    "d": shp.transform.d,
                    "ty": shp.transform.ty,
                }
            })
        return data

    def begin_batch(self):
        """
        标记：我要开始一连串的连续变换（比如拖拽）。
        我们在这里拍一次快照，供整段操作撤销。
        """
        if not self._batch_active:
            self._snapshot_for_undo()
            self._batch_active = True
            # 清 redo，跟普通操作一致
            self._redo.clear()

    def end_batch(self):
        """
        标记：这次连续变换结束了。
        之后的 translate/rotate/scale 又会开始新的一次操作。
        """
        self._batch_active = False

    def translate_and_raster(self, sid: str, dx: float, dy: float) -> List[Point]:
        self.translate_shape(sid, dx, dy)
        return self.flatten_points()