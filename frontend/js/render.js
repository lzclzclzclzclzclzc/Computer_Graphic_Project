import { state } from "./state.js";

let canvas, ctx;
export function initRender(canvasEl) {
  canvas = canvasEl;
  ctx = canvas.getContext("2d");
}
export function clear() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}
export function drawPixel(x, y, color, size = state.pixelSize) {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, size, size);
}
export function drawPreviewDot(x, y, color = "#00c853") {
  drawPixel(x, y, color, state.pixelSize + 1);
}
export function paintAll() {
  clear();
  for (const p of state.cachedPts) {
    const size = p.w ? p.w : state.pixelSize;
    drawPixel(p.x, p.y, p.color || "red",size);
  }
  if (state.selectedId) highlightShape(state.selectedId);
  if (state.rotateCenter) {
    drawPreviewDot(state.rotateCenter.x, state.rotateCenter.y, "#00ff00");
  }
}

export function highlightShape(id) {
  const pts = state.shapesById.get(id);
  if (!pts || !pts.length) return;

  // 外层描边光晕，线宽跟点的 w 绑定
  for (const p of pts) {
    const glowSize = (p.w || state.pixelSize) + 3;
    drawPixel(p.x - 1, p.y - 1, "rgba(33,150,243,0.3)", glowSize);
  }

  // 原图形
  for (const p of pts) {
    const size = p.w || state.pixelSize;
    drawPixel(p.x, p.y, p.color || "red", size);
  }
}