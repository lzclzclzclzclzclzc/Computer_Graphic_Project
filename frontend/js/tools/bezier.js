// frontend/tools/bezier.js
import { state } from "../state.js";
import { paintAll, drawPreviewDot } from "../render.js";
import { postBezier } from "../api.js";
// postLine / attachStyleFields 没用，可以删掉

let draggingIndex = -1;
let canvasElement = null;
let currentRefresh = null;   // 记住 refresh 回调


state.lastBezier = null;  // 记录上一条 Bézier 曲线的控制点

export function initBezierHandler(canvas, refresh) {
  cleanup();                // 先移除旧监听
  canvasElement = canvas;
  currentRefresh = refresh;

  canvas.addEventListener("mousedown", handleMouseDown);
  canvas.addEventListener("mousemove", handleMouseMove);
  canvas.addEventListener("mouseup", handleMouseUp);
  window.addEventListener("keydown", handleKeyDown);
}

function getMousePos(e) {
  const rect = canvasElement.getBoundingClientRect();
  return { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

async function handleMouseDown(e) {
  // 如果当前模式不是 bezier，就什么都不做（防止切到多边形后还响应）
  if (state.mode !== "bezier" || !currentRefresh) return;
  const refresh = currentRefresh;

  e.preventDefault();
  const { x, y } = getMousePos(e);

  if (e.button === 0) {
    // 左键：拖动或新增控制点
    const idx = state.points.findIndex(
      (p) => Math.hypot(p.x - x, p.y - y) < 8
    );
    if (idx !== -1) {
      draggingIndex = idx;
    } else {
      state.points.push({ x, y });
      paintAll();
      drawAllPoints();
    }
  } else if (e.button === 2) {
    // 右键：提交并清空控制点，进入下一条曲线
    if (state.points.length >= 2) {
      await postBezier({
        points: state.points,
        color: state.currentColor,
        width: state.currentWidth,
        style: state.lineStyle,
        dash_on: state.dashOn,
        dash_off: state.dashOff,
      });
    }
    state.set({ points: [] });
    await refresh();
  }
}

function handleMouseMove(e) {
  if (state.mode !== "bezier") return;
  if (draggingIndex === -1) return;
  const { x, y } = getMousePos(e);
  state.points[draggingIndex] = { x, y };

  paintAll();
  drawAllPoints();
}

function handleMouseUp() {
  if (state.mode !== "bezier") return;
  draggingIndex = -1;
}

async function handleKeyDown(e) {
  if (state.mode !== "bezier" || !currentRefresh) return;
  const refresh = currentRefresh;

  if (e.key === "Enter") {
    if (state.points.length < 2) {
      alert("至少需要两个点才能绘制 Bézier 曲线");
      return;
    }

    try {
      const savedPoints = JSON.parse(JSON.stringify(state.points));

      // 🔹1️⃣ 若有旧曲线，先平移出屏幕（假设存在 state.lastBezier）
      if (state.lastBezier && state.lastBezier.length >= 2) {
        const movedOldPoints = state.lastBezier.map(p => ({
          x: p.x + 10000,
          y: p.y + 10000,
        }));

        // 将老曲线重新提交到后端（移出可视区域）
        await postBezier({
          points: movedOldPoints,
          color: "#ccc", // 灰色表示“旧曲线”
          width: state.currentWidth,
          style: state.lineStyle,
          dash_on: state.dashOn,
          dash_off: state.dashOff,
        });
      }

      // 🔹2️⃣ 提交当前新曲线
      await postBezier({
        points: savedPoints,
        color: state.currentColor,
        width: state.currentWidth,
        style: state.lineStyle,
        dash_on: state.dashOn,
        dash_off: state.dashOff,
      });

      // 🔹3️⃣ 刷新画布
      await refresh();

      // 🔹4️⃣ 等待两帧再重绘控制折线
      await new Promise((resolve) => {
        requestAnimationFrame(() =>
          requestAnimationFrame(resolve)
        );
      });

      // 🔹5️⃣ 保存当前曲线为“上一条”以便下次移动
      state.lastBezier = JSON.parse(JSON.stringify(savedPoints));

      // 🔹6️⃣ 恢复控制点显示
      state.set({ points: savedPoints });
      drawAllPoints();

    } catch (err) {
      console.error("Bézier 绘制失败：", err);
    }
  }
}

function drawAllPoints() {
  if (!state.points.length || !canvasElement) return;

  const ctx = canvasElement.getContext("2d");
  ctx.save();
  ctx.strokeStyle = "#888";
  ctx.lineWidth = 1;
  ctx.setLineDash([4, 3]);
  ctx.beginPath();
  ctx.moveTo(state.points[0].x, state.points[0].y);
  for (let i = 1; i < state.points.length; i++) {
    ctx.lineTo(state.points[i].x, state.points[i].y);
  }
  ctx.stroke();
  ctx.restore();

  for (const p of state.points) {
    drawPreviewDot(p.x, p.y, state.currentColor);
  }
}

export function cleanup() {
  if (!canvasElement) {
    currentRefresh = null;
    draggingIndex = -1;
    return;
  }
  canvasElement.removeEventListener("mousedown", handleMouseDown);
  canvasElement.removeEventListener("mousemove", handleMouseMove);
  canvasElement.removeEventListener("mouseup", handleMouseUp);
  window.removeEventListener("keydown", handleKeyDown);
  canvasElement = null;
  currentRefresh = null;
  draggingIndex = -1;
}
