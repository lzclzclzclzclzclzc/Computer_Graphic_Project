# backend/app/domain/scene.py
from typing import List, Dict
from .shapes import Shape
import copy   # ✅ 新增

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
                if hasattr(s, "x1") and hasattr(s, "y1") and hasattr(s, "x2") and hasattr(s, "y2"):
                    s.x1 += dx; s.y1 += dy
                    s.x2 += dx; s.y2 += dy
                    moved = True
                break
        if moved:
            self._redo.clear()
        else:
            # 没找到就撤回这次快照
            if self._undo:
                self._shapes = self._undo.pop()
        return moved

    def _snapshot_for_undo(self):
        self._undo.append(copy.deepcopy(self._shapes)) #deepcopy