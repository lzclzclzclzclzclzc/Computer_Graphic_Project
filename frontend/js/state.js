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
  tool: 'select',   // 新增：'bucket' 时为填充
  fillColor: '#2ecc71',
  fillConnectivity: 4,
  fillTolerance: 0,
  moveStart: null,
  baseScale: 1,      // 本次拖拽开始时的缩放
  baseAngle: 0,      // 本次拖拽开始时的角度
  cumulativeScale: 1,// 图形当前累计缩放
  cumulativeAngle: 0, // 图形当前累计角度
  set(patch) { Object.assign(this, patch); emit(); },
};
export function onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); }
function emit() { listeners.forEach(fn => fn(state)); }