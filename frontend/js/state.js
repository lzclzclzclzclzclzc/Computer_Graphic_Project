// 超轻量“可订阅”状态
const listeners = new Set();

export const state = {
  mode: "line",                 // line | rect | circle | bezier | polygon | bspline | move | clip | bucket
  pixelSize: 2,
  currentColor: "#ff0000",      // 统一用这个作为“当前颜色”（线条 & 填充）
  currentWidth: 2,

  points: [],                   // 临时点击点
  cachedPts: [],                // 后端返回的点
  shapesById: new Map(),        // id -> 点集合
  selectedId: null,

  // 兼容旧代码：保留 fill*，但与 currentColor 同步
  fillColor: "#ff0000",
  fillConnectivity: 4,
  fillTolerance: 0,

  // 变换状态
  moveStart: null,
  baseScale: 1,
  baseAngle: 0,
  cumulativeScale: 1,
  cumulativeAngle: 0,

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
