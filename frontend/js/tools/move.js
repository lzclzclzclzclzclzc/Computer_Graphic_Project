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

/**
 * 在 move 模式下，mousedown 时调用。
 * 负责：
 * - 命中检测出哪个图形要被拖
 * - 打日志
 * - 开始一轮“批次变换”（后端合并这次拖拽成一条 undo）
 * - 绑定 mousemove / mouseup，后续拖动都走这里
 */
export function beginMoveDrag(canvas, x0, y0) {
  // 1. 命中检测：如果之前已经有选中，就继续拖那个；
  //    否则就根据当前鼠标位置挑一个最近的图形
  const pickedId = state.selectedId
    ? state.selectedId
    : pickShapeAt(x0, y0, state.cachedPts);

  // 没点中任何图形就不开始拖拽
  if (!pickedId) {
    console.log("[beginMoveDrag] abort, no hit at", x0, y0);
    return;
  }

  // 2. 打你想看到的 log（按下立即出现）
  console.log("[beginMoveDrag] start", {
    x0,
    y0,
    selectedId_before: pickedId,
  });

  // 3. 写入本次拖拽的初始状态
  //    注意：我们一次性把 selectedId 和 moveStart 都写进 state
  //    这样后面 mousemove 可以直接用
  state.set({
    selectedId: pickedId,
    moveStart: { x: x0, y: y0 },
  });

  // 4. 通知后端：我要开始一轮连续变换
  //    后端会在这个时刻 snapshot 一次，用于撤销
  postTransformBegin().catch((err) =>
    console.warn("begin_transform failed", err)
  );

  // 5. 绑定拖拽过程
  function onMouseMove(ev) {
    // 如果状态已经被清了（比如已经 mouseup 过），那就别再动
    if (!state.moveStart || !state.selectedId) return;

    const rect2 = canvas.getBoundingClientRect();
    const xNow = Math.round(ev.clientX - rect2.left);
    const yNow = Math.round(ev.clientY - rect2.top);

    const dx = xNow - state.moveStart.x;
    const dy = yNow - state.moveStart.y;

    if (dx === 0 && dy === 0) return;

    console.log("[onMouseMove] fired ▸ {dx:", dx, ", dy:", dy, "}");

    // 把这次的增量发给后端
    // 后端会移动该 shape，并返回最新整张画布的像素数组
    postTranslate({ id: state.selectedId, dx, dy })
      .then((r) => (Array.isArray(r) ? r : getPoints()))
      .then((pts) => {
        console.log(
          "[onMouseMove] got points:",
          pts && pts.length,
          pts && pts[0]
        );

        // 更新状态：
        // - cachedPts：最新像素点阵（画布数据源）
        // - moveStart：更新起点到当前鼠标位置，这样下一帧 dx/dy 就是“增量”
        state.set({
          cachedPts: pts,
          moveStart: { x: xNow, y: yNow },
        });

        // 重新建索引（shapesById），让高亮/点击检测跟上新的位置
        rebuildIndex();

        // 主动重绘一帧，保证你肉眼能看到在拖
        paintAll();
      })
      .catch((err) => {
        console.error("postTranslate failed:", err);
      });
  }
//6：滚轮缩放
  function onWheel(ev) {
    ev.preventDefault();
    if (!state.selectedId) return;
    const delta = ev.deltaY > 0 ? 0.9 : 1.1; // 每次 10%
    const cx = state.moveStart.x;            // 以鼠标位置为锚点
    const cy = state.moveStart.y;

    // 发请求
    fetch("/api/v1/scale", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id: state.selectedId, sx: delta, sy: delta, cx, cy})
    })
    .then(r => r.json())
    .then(() => refresh()); // 刷新画布
}

//7：Shift + 滚轮 旋转
  function onShiftWheel(ev) {
    ev.preventDefault();
    if (!state.selectedId) return;
    const theta = ev.deltaY > 0 ? -0.1 : 0.1; // 每次 ±0.1 弧度
    const cx = state.moveStart.x;
    const cy = state.moveStart.y;

    fetch("/api/v1/rotate", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({id: state.selectedId, theta, cx, cy})
    })
    .then(r => r.json())
    .then(() => refresh());
}
  function onMouseUp() {
    console.log("[onMouseUp] end drag");

    // 告诉后端：这轮批处理结束
    // 也就是“把整次拖拽当成一条undo记录” -> 撤销按一次就回到拖前
    postTransformEnd().catch((err) =>
      console.warn("end_transform failed", err)
    );

    // 我们希望：
    // - 松手后高亮立刻消失
    // - 画布刷新到最终状态
    // - 不需要再点一下空白区域来清除高亮
    const clearedState = {
      moveStart: null,
      selectedId: null, // 关键：这行让松手后就不高亮了
    };

    // 最后再同步一次点阵，确保和后端状态完全一致
    getPoints()
      .then((finalPts) => {
        state.set({
          cachedPts: finalPts,
          ...clearedState,
        });
        rebuildIndex();
        paintAll();
      })
      .catch((err) => {
        console.error("刷新失败 after drag:", err);
        state.set(clearedState);
        paintAll();
      });

    // 清理这次拖拽绑定的全局事件
    document.removeEventListener("mousemove", onMouseMove);
    document.removeEventListener("mouseup", onMouseUp);
    canvas.removeEventListener("wheel", onWheel);
    canvas.removeEventListener("wheel", onShiftWheel);
  }

  // 6. 全局监听鼠标移动 / 松开
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
  canvas.addEventListener("wheel", onWheel, {passive: false});
  canvas.addEventListener("wheel", ev => {if (ev.shiftKey) onShiftWheel(ev);}, {passive: false});

  console.log("[beginMoveDrag] mouse listeners attached ✅");
}

/**
 * 在画布里基于像素点命中检测 shape：
 * - 先找有没有点在同一像素
 * - 没有的话用一个半径（R=4）的小圆范围兜一下
 * 返回第一个匹配到的像素点的 id (也就是 shape id)
 */
function pickShapeAt(x, y, pts) {
  if (!pts || pts.length === 0) return null;

  // 精准命中：完全同坐标
  const exact = pts.find((p) => p.x === x && p.y === y);
  if (exact) return exact.id;

  // 模糊命中：给一点半径容忍
  const R = 4;
  for (const p of pts) {
    const dx = p.x - x;
    const dy = p.y - y;
    if (dx * dx + dy * dy <= R * R) {
      return p.id;
    }
  }

  return null;
}