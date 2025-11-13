// frontend/js/tools/move.js

import { state } from "../state.js";
import {
  postTranslate,
  getPoints,
  postTransformBegin,
  postTransformEnd,
} from "../api.js";
import { rebuildIndex } from "../picker.js";
import { paintAll } from "../render.js";

// 工具函数：命中检测
function pickShapeAt(x, y, pts) {
  if (!pts || pts.length === 0) return null;
  const exact = pts.find((p) => p.x === x && p.y === y);
  if (exact) return exact.id;
  const R = 4;
  for (const p of pts) {
    const dx = p.x - x;
    const dy = p.y - y;
    if (dx * dx + dy * dy <= R * R) return p.id;
  }
  return null;
}

// Alt 键状态
let altPressed = false;
window.addEventListener('keydown', e => { if (e.key === 'Alt') altPressed = true; });
window.addEventListener('keyup', e => { if (e.key === 'Alt') altPressed = false; });

// 主入口：在 move 模式下 mousedown 时调用
export function beginMoveDrag(canvas, x0, y0) {
  const pickedId = state.selectedId
    ? state.selectedId
    : pickShapeAt(x0, y0, state.cachedPts);

  if (!pickedId) {
    console.log("[beginMoveDrag] abort, no hit at", x0, y0);
    return;
  }

  console.log("[beginMoveDrag] start", { x0, y0, selectedId_before: pickedId });

  state.set({ selectedId: pickedId, moveStart: { x: x0, y: y0 } });
  postTransformBegin().catch((err) =>
    console.warn("begin_transform failed", err)
  );

  // 滚轮事件：缩放 / 旋转 互斥
  function onWheel(ev) {
    if (!state.selectedId) return; // 没选中不管
    ev.preventDefault(); // 真正要变换才阻止默认滚动

    let cx, cy;
    if (state.mode === "rotatePoint") {
      cx = state.rotateCenter.x;
      cy = state.rotateCenter.y;
    } else {
      cx = state.moveStart.x;
      cy = state.moveStart.y;
    }

    if (altPressed) {
      const theta = ev.deltaY > 0 ? -0.1 : 0.1;
      fetch("/api/v1/rotate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: state.selectedId, theta, cx, cy }),
      }).then(() => refresh());
    } else {
      const delta = ev.deltaY > 0 ? 0.9 : 1.1;
      fetch("/api/v1/scale", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: state.selectedId, sx: delta, sy: delta, cx, cy }),
      }).then(() => refresh());
    }
  }

  // 鼠标移动：拖拽平移
  function onMouseMove(ev) {
    if (!state.moveStart || !state.selectedId) return;

    const rect2 = canvas.getBoundingClientRect();
    const xNow = Math.round(ev.clientX - rect2.left);
    const yNow = Math.round(ev.clientY - rect2.top);

    const dx = xNow - state.moveStart.x;
    const dy = yNow - state.moveStart.y;
    if (dx === 0 && dy === 0) return;

    console.log("[onMouseMove] fired ▸ {dx:", dx, ", dy:", dy, "}");

    postTranslate({ id: state.selectedId, dx, dy })
      .then((r) => (Array.isArray(r) ? r : getPoints()))
      .then((pts) => {
        state.set({
          cachedPts: pts,
          moveStart: { x: xNow, y: yNow },
        });
        rebuildIndex();
        paintAll();
      })
      .catch((err) => console.error("postTranslate failed:", err));
  }

  // 鼠标抬起：结束拖拽
  function onMouseUp() {
    console.log("[onMouseUp] end drag");
    postTransformEnd().catch((err) =>
      console.warn("end_transform failed", err)
    );

    getPoints()
      .then((finalPts) => {
        state.set({
          cachedPts: finalPts,
          moveStart: null,
          selectedId: null,
        });
        rebuildIndex();
        paintAll();
      })
      .catch((err) => {
        console.error("刷新失败 after drag:", err);
        state.set({ moveStart: null, selectedId: null });
        paintAll();
      });

    // 清理事件监听
    document.removeEventListener("mousemove", onMouseMove);
    document.removeEventListener("mouseup", onMouseUp);
    canvas.removeEventListener("wheel", onWheel);
  }

  // 绑定事件
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
  canvas.addEventListener("wheel", onWheel, { passive: false });

  console.log("[beginMoveDrag] mouse listeners attached ✅");
}