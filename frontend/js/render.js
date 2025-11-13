// render.js
import { state } from "./state.js";

let canvas, ctx;

export function initRender(canvasEl) {
  canvas = canvasEl;
  ctx = canvas.getContext("2d", { alpha: true });
  // 关闭一切平滑
  ctx.imageSmoothingEnabled = false;
  ctx.globalCompositeOperation = "source-over";
}

function clearCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
}

const I = n => n | 0;

export function drawPixel(x, y, color, size = 1) {
  ctx.fillStyle = color;
  ctx.fillRect(I(x), I(y), I(size), I(size));
}

export function drawPreviewDot(x, y, color = "#00c853") {
  drawPixel(I(x), I(y), color, (state.pixelSize | 0) + 1);
}

export function paintAll() {
  // 清屏——用 width/height 原生像素即可
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 收集“填充像素”（id 以 fill- 开头）=> 每行的 x 列表
  const rows = new Map(); // key: y|color -> x 数组

  for (const p of state.cachedPts) {
    const isFill = String(p.id).startsWith("fill-");
    if (!isFill) {
      // 普通图形逐点画（保留你的线宽 / 颜色逻辑）
      const size = p.w ? (p.w | 0) : (state.pixelSize | 0);
      ctx.fillStyle = p.color || "red";
      ctx.fillRect((p.x | 0), (p.y | 0), size, size);
      continue;
    }
    const key = `${p.y | 0}|${p.color || "red"}`;
    if (!rows.has(key)) rows.set(key, []);
    rows.get(key).push(p.x | 0);
  }

  // 对每一行：去重 + 排序 + 合并连续段，一次 fillRect 画整段
  rows.forEach((xs, key) => {
    const [yStr, color] = key.split("|");
    const y = parseInt(yStr, 10);
    xs = Array.from(new Set(xs)).sort((a, b) => a - b);

    ctx.fillStyle = color;
    let s = xs[0], prev = xs[0];
    for (let i = 1; i <= xs.length; i++) {
      const x = xs[i];
      if (x !== prev + 1) {
        // 画 [s..prev]，高度 1px
        ctx.fillRect(s, y, prev - s + 1, 1);
        s = x;
      }
      prev = x;
    }
  });

  if (state.selectedId) highlightShape(state.selectedId);
  if (state.rotateCenter) {
    drawPreviewDot(state.rotateCenter.x, state.rotateCenter.y, "#00ff00");
  }
}

export function highlightShape(id) {
  const pts = state.shapesById.get(id);
  if (!pts || !pts.length) return;

  for (const p of pts) {
    const glowSize = ((p.w | 0) || (state.pixelSize | 0)) + 3;
    drawPixel((p.x - 1) | 0, (p.y - 1) | 0, "rgba(33,150,243,0.3)", glowSize);
  }
  for (const p of pts) {
    const size = (p.w | 0) || (state.pixelSize | 0);
    drawPixel(p.x | 0, p.y | 0, p.color || "red", size);
  }
}