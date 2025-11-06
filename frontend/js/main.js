import { getPoints, postUndo, clearCanvas, postTranslate } from "./api.js";
import { state, onChange } from "./state.js";
import { initRender, paintAll } from "./render.js";
import { handleClickLine } from "./tools/line.js";
import { handleClickRect } from "./tools/rect.js";
import {  beginMoveDrag } from "./tools/move.js";
import { handleClickCircle } from "./tools/circle.js";
import { handleClickBezier } from "./tools/bezier.js";
import { handleClickPolygon } from "./tools/polygon.js";
import { handleClickBSpline } from "./tools/BSpline.js";
import { handleClickArc } from "./tools/arc.js";
import { handleClickClip } from "./tools/clip.js";
import { rebuildIndex, pickShapeByPoint } from "./picker.js";
const canvas = document.getElementById("canvas");
initRender(canvas);
canvas.addEventListener("contextmenu", (e) => e.preventDefault());

canvas.addEventListener("wheel", e => {
  if (state.mode !== "rotatePoint" || !state.selectedId || !state.rotateCenter) return;
  e.preventDefault();
  const theta = e.deltaY > 0 ? 0.1 : -0.1;
  fetch("/api/v1/rotate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      id: state.selectedId,
      theta,
      cx: state.rotateCenter.x,
      cy: state.rotateCenter.y
    })
  }).then(() => refresh());
}, { passive: false });

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
    rotatePoint: document.getElementById("rotatePointBtn"),
    bspline: document.getElementById("bsplineBtn"),
    arc: document.getElementById("arcBtn"),
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

document.getElementById("rotatePointBtn").onclick = () =>
  state.set({ mode: "rotatePoint", selectedId: null, moveStart: null, points: [], rotateCenter: null });

document.getElementById("arcBtn").onclick = () =>
  state.set({ mode: "arc", selectedId: null, moveStart: null, points: [] });

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

document.getElementById("bsplineBtn").onclick = () =>
  state.set({ mode: "bspline", selectedId: null, moveStart: null, points: [] });

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
  if (state.mode === "arc")    return handleClickArc(x, y, refresh);

  // 2. 只有在“操作类模式”下才去选中
  if (state.mode === "move" || state.mode === "clip") {
    const hit = pickShapeByPoint(x, y, 12); // 12 是选中的容差，可调
    state.set({ selectedId: hit ? hit.id : null });
  }

  //3.选中点旋转
  if (state.mode === "rotatePoint") {
  // 第一下：没中心点 → 设中心
    if (!state.rotateCenter) {
      state.set({ rotateCenter: { x, y } });
      return;
    }
  // 第二下：按普通 move/clip 逻辑去“选中”
    const hit = pickShapeByPoint(x, y, 12);
    state.set({ selectedId: hit ? hit.id : null });
    return;
  }

  // 其他模式（bezier / polygon）点一下啥也不做，让它们自己在 mousedown 里处理
});

//esc监听
window.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    state.set({ rotateCenter: null });
  }
});

// ------- mousedown --------
// 按下：进入多段绘制 (bezier/polygon) 或进入拖拽 (move)
canvas.addEventListener("mousedown", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x0 = Math.round(e.clientX - rect.left);
  const y0 = Math.round(e.clientY - rect.top);

  if (state.mode === "move") {
    beginMoveDrag(canvas, x0, y0);
    return;
  }

  if (state.mode === "bezier") {
    return handleClickBezier(x0, y0, e.button, refresh);
  }

  if (state.mode === "polygon") {
    return handleClickPolygon(x0, y0, e.button, refresh);
  }

  if (state.mode === "clip") {
  return handleClickClip(x0, y0, e.button, refresh);
  }

  if (state.mode === "bspline") {
    return handleClickBSpline(x0, y0, e.button, refresh);
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