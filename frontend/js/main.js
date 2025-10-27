import { getPoints, postUndo, clearCanvas, postTranslate } from "./api.js";
import { state, onChange } from "./state.js";
import { initRender, paintAll } from "./render.js";
import { rebuildIndex } from "./picker.js";
import { handleClickLine } from "./tools/line.js";
import { handleClickRect } from "./tools/rect.js";
import { handleClickMove, beginMoveDrag } from "./tools/move.js";
import { handleClickCircle } from "./tools/circle.js";
import { handleClickBezier } from "./tools/bezier.js";
import { handleClickPolygon } from "./tools/polygon.js";

const canvas = document.getElementById("canvas");
initRender(canvas);
canvas.addEventListener("contextmenu", (e) => e.preventDefault());

async function refresh() {
  try {
    const pts = await getPoints();
    state.set({ cachedPts: pts }); // 触发重画
    rebuildIndex();
  } catch (e) {
    console.error("刷新失败：", e);
  }
}

function updateToolbarActive() {
  const map = {
    line: document.getElementById("lineBtn"),
    rect: document.getElementById("rectBtn"),
    circle: document.getElementById("circleBtn"),
    move: document.getElementById("moveBtn"),
    bezier: document.getElementById("bezierBtn"),
    polygon: document.getElementById("polygonBtn"),
    clean: document.getElementById("clearBtn"),
  };
  document.querySelectorAll(".controls button").forEach(btn => btn.classList.remove("active"));
  const el = map[state.mode];
  if (el) el.classList.add("active");
}

// ------- toolbar 按钮事件 --------
document.getElementById("lineBtn").onclick = () =>
  state.set({ mode: "line", selectedId: null, moveStart: null, points: [] });

document.getElementById("rectBtn").onclick = () =>
  state.set({ mode: "rect", selectedId: null, moveStart: null, points: [] });

document.getElementById("moveBtn").onclick = () =>
  state.set({ mode: "move", selectedId: null, moveStart: null, points: [] });

document.getElementById("circleBtn").onclick = () =>
  state.set({ mode: "circle", selectedId: null, moveStart: null, points: [] });

document.getElementById("undoBtn").onclick = async () => {
  try {
    await postUndo();
  } catch (e) {
    console.error("撤销失败：", e);
  } finally {
    state.set({ points: [], selectedId: null, moveStart: null });
    await refresh();
  }
};

document.getElementById("clearBtn").onclick = async () => {
  try {
    await clearCanvas();
  } catch (e) {
    console.error("清空画布失败：", e);
  } finally {
    state.set({ points: [], selectedId: null, moveStart: null });
    await refresh();
  }
};

document.getElementById("bezierBtn").onclick = () =>
  state.set({ mode: "bezier", selectedId: null, moveStart: null, points: [] });

document.getElementById("polygonBtn").onclick = () =>
  state.set({ mode: "polygon", selectedId: null, moveStart: null, points: [] });

const colorEl = document.getElementById("colorPicker");
if (colorEl) {
  colorEl.addEventListener("input", (e) => {
    state.set({ currentColor: e.target.value });
  });
}

const widthEl = document.getElementById("widthPicker");
const widthLabel = document.getElementById("widthLabel");
if (widthEl) {
  widthEl.addEventListener("input", (e) => {
    const v = parseInt(e.target.value, 10) || 1;
    state.set({ currentWidth: v });
    if (widthLabel) widthLabel.textContent = String(v);
  });
}

// ------- click --------
// 单击：画线/矩形/圆/选中要移动的 shape
canvas.addEventListener("click", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);

  if (state.mode === "line")   return handleClickLine(x, y, refresh);
  if (state.mode === "rect")   return handleClickRect(x, y, refresh);
  if (state.mode === "circle") return handleClickCircle(x, y, refresh);
  if (state.mode === "move")   return handleClickMove(x, y); // 只负责选中
});

// ------- mousedown --------
// 按下：进入多段绘制 (bezier/polygon) 或进入拖拽 (move)
canvas.addEventListener("mousedown", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x0 = Math.round(e.clientX - rect.left);
  const y0 = Math.round(e.clientY - rect.top);
  console.log("[mousedown] mode=", state.mode, "at", x0, y0);
  if (state.mode === "bezier") {
    return handleClickBezier(x0, y0, e.button, refresh);
  }
  if (state.mode === "polygon") {
    return handleClickPolygon(x0, y0, e.button, refresh);
  }
  if (state.mode === "move") {
    return beginMoveDrag(canvas, x0, y0); // <--- 用 tools/move.js 的函数
  }

});

// 状态变化 -> 视觉更新（高亮/线宽/颜色等）
onChange(() => {
  updateToolbarActive();
  paintAll();
});

// 第一次加载
refresh();
updateToolbarActive();