# backend/app/domain/scene.py

from typing import List, Dict, Optional
import copy
from .shapes import Shape, Polygon
from .geom import clip_polygon_rect  # <--- 新的
from .shapes import Shape  # 假设你的 Line / Rectangle / Circle / Bezier / Polygon 都继承了 Shape
from .shapes import Line, Rectangle, Circle, Bezier, Polygon
from .geom import Mat2x3, clip_polygon_rect   # clip_polygon_rect 就是你原来用的那个

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

    def clip_polygon_by_rect(self, shape_id: str,
                             x1: float, y1: float,
                             x2: float, y2: float) -> bool:
        """把指定的 Polygon 用一个轴对齐矩形裁剪"""
        if shape_id not in self._shapes:
            return False

        shp = self._shapes[shape_id]
        if not isinstance(shp, Polygon):
            # 这里你也可以选择：矩形也转成4点的polygon再裁
            return False

        # 1. 先把多边形的“局部点”变成“世界坐标点”
        world_pts = []
        for p in shp.points:
            X, Y = shp.transform.apply(p["x"], p["y"])
            world_pts.append({"x": X, "y": Y})

        # 2. 规范化窗口
        x_min, x_max = sorted([x1, x2])
        y_min, y_max = sorted([y1, y2])

        # 3. 真正裁剪
        clipped = clip_polygon_rect(world_pts, x_min, y_min, x_max, y_max)

        # 4. 拍快照
        self._snapshot_for_undo()

        if not clipped:
            # 全剪掉了，就删图形
            del self._shapes[shape_id]
            self._redo.clear()
            return True

        # 5. 用裁好的点生成一个新的 polygon，注意我们让它回到“无变换”的状态
        new_poly = Polygon(
            points=clipped,
            color=shp.color,
            pen_width=shp.pen_width,
            style=getattr(shp, "style", "solid"),
            dash_on=getattr(shp, "dash_on", 0),
            dash_off=getattr(shp, "dash_off", 0),
            closed=getattr(shp, "closed", True),
        )

        # 覆盖原来的
        self._shapes[shape_id] = new_poly
        self._redo.clear()
        return True

    def clip_polygon_by_rect_and_raster(self, shape_id, x1, y1, x2, y2):
        ok = self.clip_polygon_by_rect(shape_id, x1, y1, x2, y2)
        # 不管成不成，一律把当前场景点展平给前端
        return self.flatten_points()

    from .shapes import Line, Rectangle, Circle, Bezier, Polygon
    from .geom import Mat2x3, clip_polygon_rect  # clip_polygon_rect 就是你原来用的那个

    def clip_shape_by_rect_and_raster(self, shape_id, x1, y1, x2, y2):
        """
        通用裁剪：优先走“多边形版”（你原来那套），
        不是多边形再按类型慢慢处理，最后一律 flatten_points 返回给前端
        """
        shp = self._shapes.get(shape_id)
        if shp is None:
            return self.flatten_points()

        # 归一化窗口
        x_min, x_max = sorted([x1, x2])
        y_min, y_max = sorted([y1, y2])

        # 1) 如果本来就是 Polygon，就用你原来的那条，别动
        if isinstance(shp, Polygon):
            self.clip_polygon_by_rect(shape_id, x1, y1, x2, y2)
            return self.flatten_points()

        # 2) Line：用简单线段裁剪
        if isinstance(shp, Line):
            # 先转世界坐标
            X1, Y1 = shp.transform.apply(shp.x1, shp.y1)
            X2, Y2 = shp.transform.apply(shp.x2, shp.y2)

            # Liang–Barsky 简版
            dx, dy = X2 - X1, Y2 - Y1
            p = [-dx, dx, -dy, dy]
            q = [X1 - x_min, x_max - X1, Y1 - y_min, y_max - Y1]
            u1, u2 = 0.0, 1.0
            ok = True
            for pi, qi in zip(p, q):
                if pi == 0:
                    if qi < 0:
                        ok = False
                        break
                    continue
                t = qi / pi
                if pi < 0:
                    if t > u2:
                        ok = False
                        break
                    if t > u1:
                        u1 = t
                else:
                    if t < u1:
                        ok = False
                        break
                    if t < u2:
                        u2 = t
            self._snapshot_for_undo()
            if not ok:
                # 全剪没了
                del self._shapes[shape_id]
                self._redo.clear()
                return self.flatten_points()

            nx1 = X1 + u1 * dx
            ny1 = Y1 + u1 * dy
            nx2 = X1 + u2 * dx
            ny2 = Y1 + u2 * dy
            # 写回去，清 transform
            shp.transform = Mat2x3.identity()
            shp.x1, shp.y1 = nx1, ny1
            shp.x2, shp.y2 = nx2, ny2
            self._redo.clear()
            return self.flatten_points()

        # 3) Rectangle：转成4点多边形再裁
        if isinstance(shp, Rectangle):
            # 先取局部四个角
            l = min(shp.x1, shp.x2)
            r = max(shp.x1, shp.x2)
            t = min(shp.y1, shp.y2)
            b = max(shp.y1, shp.y2)
            corners = [
                {"x": l, "y": t},
                {"x": r, "y": t},
                {"x": r, "y": b},
                {"x": l, "y": b},
            ]
            # 转世界坐标
            world = []
            for c in corners:
                X, Y = shp.transform.apply(c["x"], c["y"])
                world.append({"x": X, "y": Y})
            # 用你原来的裁剪函数
            clipped = clip_polygon_rect(world, x_min, y_min, x_max, y_max)
            self._snapshot_for_undo()
            # 覆盖成 Polygon
            poly = Polygon(
                points=clipped,
                color=shp.color,
                pen_width=shp.pen_width,
                style=getattr(shp, "style", "solid"),
                dash_on=getattr(shp, "dash_on", 0),
                dash_off=getattr(shp, "dash_off", 0),
                closed=True,
            )
            poly.id = shp.id
            self._shapes[shape_id] = poly

            self._redo.clear()
            return self.flatten_points()

        if isinstance(shp, Circle):
            raw = shp.rasterize()
            world = [{"x": p["x"], "y": p["y"]} for p in raw]
            clipped = clip_polygon_rect(world, x_min, y_min, x_max, y_max)
            self._snapshot_for_undo()
            poly = Polygon(
                points=clipped,
                color=shp.color,
                pen_width=shp.pen_width,
                style=getattr(shp, "style", "solid"),
                dash_on=getattr(shp, "dash_on", 0),
                dash_off=getattr(shp, "dash_off", 0),
                closed=True,
            )
            poly.id = shp.id
            self._shapes[shape_id] = poly

            self._redo.clear()
            return self.flatten_points()

        # 5) Bézier / 曲线：用“折线裁剪”，只留下在窗口里的曲线，不闭合
        if isinstance(shp, Bezier):
            # 先拿到世界坐标下的采样点（是按顺序的）
            samples = shp.rasterize()  # [{'x':..,'y':..}, ...] 世界坐标
            if not samples or len(samples) < 2:
                return self.flatten_points()

            xmin, xmax = sorted([x1, x2])
            ymin, ymax = sorted([y1, y2])

            # 段裁剪：Liang–Barsky，小函数
            def clip_seg(p1, p2):
                x1_, y1_ = p1["x"], p1["y"]
                x2_, y2_ = p2["x"], p2["y"]
                dx, dy = x2_ - x1_, y2_ - y1_
                p = [-dx, dx, -dy, dy]
                q = [x1_ - xmin, xmax - x1_, y1_ - ymin, ymax - y1_]
                u1, u2 = 0.0, 1.0
                for pi, qi in zip(p, q):
                    if pi == 0:
                        if qi < 0:
                            return None
                        continue
                    t = qi / pi
                    if pi < 0:
                        if t > u2:
                            return None
                        if t > u1:
                            u1 = t
                    else:
                        if t < u1:
                            return None
                        if t < u2:
                            u2 = t
                sx = x1_ + u1 * dx
                sy = y1_ + u1 * dy
                ex = x1_ + u2 * dx
                ey = y1_ + u2 * dy
                return {"x": sx, "y": sy}, {"x": ex, "y": ey}

            self._snapshot_for_undo()

            out_pts = []
            last_end = None

            for i in range(len(samples) - 1):
                seg = clip_seg(samples[i], samples[i + 1])
                if not seg:
                    continue
                s, e = seg
                # 起点
                if not out_pts:
                    out_pts.append({"x": int(round(s["x"])), "y": int(round(s["y"]))})
                else:
                    # 如果这一段的起点跟上一次的终点不一样，说明中间有一截在外面
                    # 我们就直接接到新的起点，会是一条直线，这里你愿意的话也可以分成多个 shape
                    if out_pts[-1]["x"] != int(round(s["x"])) or out_pts[-1]["y"] != int(round(s["y"])):
                        out_pts.append({"x": int(round(s["x"])), "y": int(round(s["y"]))})
                # 终点
                out_pts.append({"x": int(round(e["x"])), "y": int(round(e["y"]))})

            if not out_pts:
                # 全在外面，删掉就好
                del self._shapes[shape_id]
                self._redo.clear()
                return self.flatten_points()

            # 只对 Bézier 这一支：用不闭合的 polygon
            poly = Polygon(
                points=out_pts,
                color=shp.color,
                pen_width=shp.pen_width,
                style=getattr(shp, "style", "solid"),
                dash_on=getattr(shp, "dash_on", 0),
                dash_off=getattr(shp, "dash_off", 0),
                closed=False,  # 曲线保持不闭合
            )
            poly.id = shp.id
            self._shapes[shape_id] = poly

            self._redo.clear()
            return self.flatten_points()

        # 其它类型：先不管，直接返回现状
        return self.flatten_points()
