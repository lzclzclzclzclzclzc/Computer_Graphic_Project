// 超轻量“可订阅”状态
const listeners = new Set();
export const state = {
  mode: "line",                 // line | rect | move
  pixelSize: 2,
  currentColor: "#ff0000",
  currentWidth: 2,
  points: [],                   // 临时点击点
  cachedPts: [],                // 后端返回的点
  shapesById: new Map(),        // id -> 点集合
  selectedId: null,
  moveStart: null,
  set(patch) { Object.assign(this, patch); emit(); },
};
export function onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); }
function emit() { listeners.forEach(fn => fn(state)); }