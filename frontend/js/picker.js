import { state } from "./state.js";

const hypot = Math.hypot;
function dist(x1, y1, x2, y2) { return hypot(x1 - x2, y1 - y2); }

function minDistToPointCloud(points, x, y, step = 1) {
  let best = Infinity;
  for (let i = 0; i < points.length; i += step) {
    const p = points[i];
    const d = dist(p.x, p.y, x, y);
    if (d < best) best = d;
    if (best === 0) break;
  }
  return best;
}

export function rebuildIndex() {
  const map = new Map();
  for (const p of state.cachedPts) {
    if (!p.id) continue;
    const arr = map.get(p.id) || [];
    arr.push(p);
    map.set(p.id, arr);
  }
  state.shapesById = map;
}

export function pickShapeByPoint(x, y, threshold = 12) {
  let winnerId = null, best = Infinity;
  for (const [id, pts] of state.shapesById.entries()) {
    const d = minDistToPointCloud(pts, x, y, 1);
    if (d < best) { best = d; winnerId = id; }
  }
  if (best <= threshold) return { id: winnerId, dist: best };
  return null;
}