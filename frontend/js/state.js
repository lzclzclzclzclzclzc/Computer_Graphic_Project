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
  baseScale: 1,      // 本次拖拽开始时的缩放
  baseAngle: 0,      // 本次拖拽开始时的角度
  cumulativeScale: 1,// 图形当前累计缩放
  cumulativeAngle: 0, // 图形当前累计角度
  set(patch) { Object.assign(this, patch); emit(); },
  lineStyle: "solid",   // "solid" | "dash-6-4" 等
  dashOn: 0,
  dashOff: 0,
};
export function onChange(fn) { listeners.add(fn); return () => listeners.delete(fn); }
function emit() { listeners.forEach(fn => fn(state)); }

export function setLineStyleFromValue(v) {
  // v 来自下拉框的 value，比如 "solid" / "dash-6-4" / "dash-10-6"
  let on = 0, off = 0;
  if (v.startsWith("dash-")) {
    const parts = v.split("-");
    on = parseInt(parts[1] || "6", 10);
    off = parseInt(parts[2] || "4", 10);
    if (!Number.isFinite(on) || !Number.isFinite(off) || on <= 0 || off <= 0) {
      on = 6; off = 4; // 兜底
    }
  }
  state.set({ lineStyle: v, dashOn: on, dashOff: off });
}
