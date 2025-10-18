# backend/app/domain/scene.py
from typing import List, Dict
from .shapes import Shape

Point = Dict[str, int]

class Scene:
    def __init__(self):
        self._shapes: List[Shape] = []
        self._undo: List[List[Shape]] = []  # 撤销栈
        self._redo: List[List[Shape]] = []  # 重做栈

    def add(self, shape: Shape):
        self._snapshot_for_undo()
        self._shapes.append(shape)
        self._redo.clear()

    def undo(self):
        if not self._undo:
            return
        self._redo.append(self._shapes[:])
        self._shapes = self._undo.pop()

    def redo(self):
        if not self._redo:
            return
        self._undo.append(self._shapes[:])
        self._shapes = self._redo.pop()

    def flatten_points(self) -> List[Point]:
        pts: List[Point] = []
        for s in self._shapes:
            pts.extend(s.rasterize())
        return pts

    def _snapshot_for_undo(self):
        self._undo.append(self._shapes[:])