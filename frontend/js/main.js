import { getPoints, postUndo, clearCanvas, postTranslate } from "./api.js";
import { state, onChange } from "./state.js";
import { initRender, paintAll } from "./render.js";
import { handleClickLine } from "./tools/line.js";
import { handleClickRect } from "./tools/rect.js";
import {  beginMoveDrag } from "./tools/move.js";
import { handleClickCircle } from "./tools/circle.js";
import { handleClickBezier } from "./tools/bezier.js";
import { handleClickPolygon } from "./tools/polygon.js";
import { handleClickClip } from "./tools/clip.js";
import { rebuildIndex, pickShapeByPoint } from "./picker.js";
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
document.getElementById("clipBtn").onclick = () =>
  state.set({ mode: "clip",  moveStart: null, points: [] });



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
// 单击：画线/矩形/圆；如果是 move / clip，就当成“点选”
canvas.addEventListener("click", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);

  // 1. 画图形的几种模式，保持原样
  if (state.mode === "line")   return handleClickLine(x, y, refresh);
  if (state.mode === "rect")   return handleClickRect(x, y, refresh);
  if (state.mode === "circle") return handleClickCircle(x, y, refresh);

  // 2. 只有在“操作类模式”下才去选中
  if (state.mode === "move" || state.mode === "clip") {
    const hit = pickShapeByPoint(x, y, 12); // 12 是选中的容差，可调
    state.set({ selectedId: hit ? hit.id : null });
  }

  // 其他模式（bezier / polygon）点一下啥也不做，让它们自己在 mousedown 里处理
});

// ------- mousedown --------
// 按下：进入多段绘制 (bezier/polygon) 或进入拖拽 (move)
canvas.addEventListener("mousedown", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x0 = Math.round(e.clientX - rect.left);
  const y0 = Math.round(e.clientY - rect.top);

  // 1. move 模式是拖拽，不能被别的逻辑抢走
  if (state.mode === "move") {
    beginMoveDrag(canvas, x0, y0);
    return;
  }

  // 2. bezier 模式：一击一击加控制点
  if (state.mode === "bezier") {
    return handleClickBezier(x0, y0, e.button, refresh);
  }

  // 3. polygon 模式：一击一击加多边形点
  if (state.mode === "polygon") {
    return handleClickPolygon(x0, y0, e.button, refresh);
  }
  if (state.mode === "clip") {
  return handleClickClip(x0, y0, e.button, refresh);
}

  // 4. clip 模式等会儿这里也要加（下面第2节说）
});

// 状态变化 -> 视觉更新（高亮/线宽/颜色等）
onChange(() => {
  updateToolbarActive();
  paintAll();
});

// 第一次加载
refresh();
updateToolbarActive();