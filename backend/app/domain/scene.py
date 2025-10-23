# backend/app/domain/scene.py
from typing import List, Dict
from .shapes import Shape
import copy

Point = Dict[str, int]

class Scene:
    def __init__(self):
        self._shapes: List[Shape] = []
        self._undo: List[List[Shape]] = []
        self._redo: List[List[Shape]] = []

    def add(self, shape: Shape):
        self._snapshot_for_undo()
        self._shapes.append(shape)
        self._redo.clear()

    def undo(self):
        if not self._undo:
            return
        self._redo.append(copy.deepcopy(self._shapes)) #deepcopy
        self._shapes = self._undo.pop()

    def redo(self):
        if not self._redo:
            return
        self._undo.append(copy.deepcopy(self._shapes)) #deepcopy
        self._shapes = self._redo.pop()

    def flatten_points(self) -> List[Point]:
        pts: List[Point] = []
        for s in self._shapes:
            pts.extend(s.rasterize())
        return pts

    def move(self, sid: str, dx: int, dy: int) -> bool:
        if not sid or (dx == 0 and dy == 0):
            return False
        self._snapshot_for_undo()
        moved = False

        for s in self._shapes:
            if getattr(s, "id", None) == sid:
                # 动态检查所有以 x 或 y 开头的坐标属性（避免遗漏 x3,y3 或 cx,cy）
                for attr in dir(s):
                    if attr.startswith("x") and isinstance(getattr(s, attr), (int, float)):
                        setattr(s, attr, getattr(s, attr) + dx)
                    elif attr.startswith("y") and isinstance(getattr(s, attr), (int, float)):
                        setattr(s, attr, getattr(s, attr) + dy)
                moved = True
                break

        if moved:
            self._redo.clear()
        else:
            if self._undo:
                self._shapes = self._undo.pop()

        return moved

    def _snapshot_for_undo(self):
        self._undo.append(copy.deepcopy(self._shapes)) #deepcopy