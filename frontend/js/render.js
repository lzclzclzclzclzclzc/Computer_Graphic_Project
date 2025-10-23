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
}
export function highlightShape(id) {
  const pts = state.shapesById.get(id);
  if (!pts || !pts.length) return;
  for (const p of pts) {
    drawPixel(p.x - 1, p.y - 1, "rgba(33,150,243,0.35)", state.pixelSize + 2);
  }
  for (const p of pts) {
    drawPixel(p.x, p.y, p.color || "red", state.pixelSize);
  }
}