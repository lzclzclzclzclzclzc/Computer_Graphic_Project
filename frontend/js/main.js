import { getPoints, postUndo, clearCanvas } from "./api.js";
import { state, onChange } from "./state.js";
import { initRender, paintAll } from "./render.js";
import { rebuildIndex } from "./picker.js";
import { handleClickLine } from "./tools/line.js";
import { handleClickRect } from "./tools/rect.js";
import { handleClickMove } from "./tools/move.js";
import { handleClickCircle } from "./tools/circle.js";
import { handleClickBezier } from "./tools/bezier.js";

const canvas = document.getElementById("canvas");
initRender(canvas);

async function refresh() {
  try {
    const pts = await getPoints();
    state.cachedPts = pts;
    rebuildIndex();
    paintAll();
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
    clean: document.getElementById("clearBtn"),
  };
  // 先清空
  document.querySelectorAll(".controls button").forEach(btn => btn.classList.remove("active"));
  // 根据当前状态加高亮
  const el = map[state.mode];
  if (el) el.classList.add("active");
}

// 事件绑定
document.getElementById("lineBtn").onclick = () => state.set({ mode: "line", selectedId: null, moveStart: null, points: [] });
document.getElementById("rectBtn").onclick = () => state.set({ mode: "rect", selectedId: null, moveStart: null, points: [] });
document.getElementById("moveBtn").onclick = () => state.set({ mode: "move", selectedId: null, moveStart: null, points: [] });
document.getElementById("circleBtn").onclick = () => state.set({ mode: "circle", selectedId: null, moveStart: null, points: [] });
document.getElementById("undoBtn").onclick = async () => {
  try { await postUndo(); } catch (e) { console.error("撤销失败：", e); }
  finally { state.set({ points: [], selectedId: null, moveStart: null }); await refresh(); }
};
document.getElementById("clearBtn").onclick = async () => {
  try { await clearCanvas(); } catch (e) { console.error("清空画布失败：", e); }
  finally { state.set({ points: [], selectedId: null, moveStart: null }); await refresh(); }
};
document.getElementById("bezierBtn").onclick = () =>
  state.set({ mode: "bezier", selectedId: null, moveStart: null, points: [] });


const colorEl = document.getElementById("colorPicker");
if (colorEl) colorEl.addEventListener("input", (e) => state.set({ currentColor: e.target.value }));

const widthEl = document.getElementById("widthPicker");
const widthLabel = document.getElementById("widthLabel");
if (widthEl) {
  widthEl.addEventListener("input", (e) => {
    const v = parseInt(e.target.value, 10) || 1;
    state.set({ currentWidth: v });
    if (widthLabel) widthLabel.textContent = String(v);
  });
}

canvas.addEventListener("click", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);

  if (state.mode === "line") return handleClickLine(x, y, refresh);
  if (state.mode === "rect") return handleClickRect(x, y, refresh);
  if (state.mode === "circle") return handleClickCircle(x, y, refresh);
  if (state.mode === "move") return handleClickMove(x, y, refresh);
  if (state.mode === "bezier") return handleClickBezier(x, y, refresh);
});

// 状态变化时重画（比如高亮/颜色更改等）
onChange(() =>{
  updateToolbarActive();
  paintAll();
});


// 首次刷新
refresh();
updateToolbarActive();