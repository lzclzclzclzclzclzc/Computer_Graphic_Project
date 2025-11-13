// tools/bezier.js
import { state } from "../state.js";
import { paintAll, drawPreviewDot } from "../render.js";
import { postBezier } from "../api.js";
import { postLine, attachStyleFields } from "../api.js";
let draggingIndex = -1;
let canvasElement = null;

export function initBezierHandler(canvas, refresh) {
  cleanup();
  canvasElement = canvas;

  canvas.addEventListener("mousedown", (e) => handleMouseDown(e, refresh));
  canvas.addEventListener("mousemove", handleMouseMove);
  canvas.addEventListener("mouseup", handleMouseUp);
  window.addEventListener("keydown", (e) => handleKeyDown(e, refresh));
}

function getMousePos(e) {
  const rect = canvasElement.getBoundingClientRect();
  return { x: e.clientX - rect.left, y: e.clientY - rect.top };
}

async function handleMouseDown(e, refresh) {
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
    e.preventDefault();
    if (state.points.length >= 2) {
      await postBezier({
        points: state.points,
        color: state.currentColor,
        width: state.currentWidth,
        style: state.lineStyle,          // 新增
    dash_on: state.dashOn,           // 新增
    dash_off: state.dashOff,         // 新增
      });
    }
    state.set({ points: [] });
    await refresh();
  }
}

function handleMouseMove(e) {
  if (draggingIndex === -1) return;
  const { x, y } = getMousePos(e);
  state.points[draggingIndex] = { x, y };

  paintAll();
  drawAllPoints();
}

function handleMouseUp() {
  draggingIndex = -1;
}

async function handleKeyDown(e, refresh) {
  if (e.key === "Enter") {
    if (state.points.length < 2) {
      alert("至少需要两个点才能绘制 Bézier 曲线");
      return;
    }

    try {
      const savedPoints = JSON.parse(JSON.stringify(state.points));

      await postBezier({
        points: savedPoints,
        color: state.currentColor,
        width: state.currentWidth,
      });

      await refresh();

      await new Promise(resolve => {
        requestAnimationFrame(() => requestAnimationFrame(resolve));
      });

      state.set({ points: savedPoints });
      drawAllPoints();

    } catch (err) {
      console.error("Bézier 绘制失败：", err);
    }
  }
}

function drawAllPoints() {
  if (!state.points.length) return;

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

function cleanup() {
  if (!canvasElement) return;
  canvasElement.removeEventListener("mousedown", handleMouseDown);
  canvasElement.removeEventListener("mousemove", handleMouseMove);
  canvasElement.removeEventListener("mouseup", handleMouseUp);
  window.removeEventListener("keydown", handleKeyDown);
  canvasElement = null;
}
