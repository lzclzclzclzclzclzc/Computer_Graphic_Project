// frontend/js/tools/fill.js
import { postFill } from "../api.js";
import { state } from "../state.js";

function uniqSorted(arr) { return Array.from(new Set(arr)).sort((a, b) => a - b); }

export async function handleClickBucket(canvas, x, y, refresh) {
  const res = await postFill({
    x, y,
    color: state.currentColor,                 // ← 用线条颜色
    connectivity: state.fillConnectivity || 4,
    tol: state.fillTolerance || 0,
    w: canvas.width, h: canvas.height,
  });

  // 兼容旧后端（返回 points 数组）
  if (Array.isArray(res)) {
    console.warn("[FILL] 后端返回旧格式（points 数组），无法精准获取 fill_id。建议更新后端到返回 {points, fill_id, pixels}。");
    state.set({ cachedPts: res });
    await refresh();
    return;
  }

  const { points, fill_id, pixels } = res;
  state.set({ cachedPts: points });

  if (!fill_id || !pixels || pixels.length === 0) {
    console.warn("[FILL] 本次没有产生新的填充（可能颜色相同或点在边界外）");
    await refresh();
    return;
  }

  console.log(`[FILL] 新建 ${fill_id}，像素数=${pixels.length}`);
  console.table(pixels.slice(0, 50).map(p => ({ x: p.x|0, y: p.y|0, color: p.color })));

  // 行区间摘要（便于排查）
  const rows = new Map();
  for (const p of pixels) {
    const y0 = p.y | 0;
    if (!rows.has(y0)) rows.set(y0, []);
    rows.get(y0).push(p.x | 0);
  }
  const spans = [];
  rows.forEach((xs, y0) => {
    xs = uniqSorted(xs);
    let s = xs[0], prev = xs[0];
    for (let i = 1; i <= xs.length; i++) {
      const x1 = xs[i];
      if (x1 !== prev + 1) {
        spans.push({ y: y0, x1: s, x2: prev, width: prev - s + 1 });
        s = x1;
      }
      prev = x1;
    }
  });
  console.log("[FILL] 行区间摘要（前50段）:");
  console.table(spans.slice(0, 50));

  await refresh();
}