// frontend/js/api.js

const API = "/api/v1";

// --- scene read ---

export async function getPoints() {
  const r = await fetch(`${API}/points`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /points ${r.status}`);
  return r.json(); // -> [ {x,y,color,id,w}, ... ]
}

export async function getSceneState() {
  // 可选：调 /scene (如果你后端加了 dump_scene_state)
  const r = await fetch(`${API}/scene`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /scene ${r.status}`);
  return r.json();
}

// --- create shapes ---

export async function postLine(payload) {
  const r = await fetch(`${API}/lines`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`POST /lines ${r.status}`);
  return r.json(); // 服务端 add_line 返回 flatten_points()
}

export async function postRect(payload) {
  const r = await fetch(`${API}/rectangles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`POST /rectangles ${r.status}`);
  return r.json();
}

export async function postCircle(payload) {
  const r = await fetch(`${API}/circles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ error: "请求失败" }));
    throw new Error(err.error || `HTTP ${r.status}`);
  }
  return r.json();
}

export async function postBezier(payload) {
  const r = await fetch(`${API}/bezier`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ error: "请求失败" }));
    throw new Error(err.error || `HTTP ${r.status}`);
  }
  return r.json();
}

export async function postBSpline(payload) {
  const r = await fetch(`${API}/bspline`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ error: "请求失败" }));
    throw new Error(err.error || `HTTP ${r.status}`);
  }
  return r.json();
}

export async function postPolygon(payload) {
  const r = await fetch(`${API}/polygons`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ error: "请求失败" }));
    throw new Error(err.error || `HTTP ${r.status}`);
  }
  return r.json();
}

export async function postArc(payload) {
  const r = await fetch(`${API}/arc`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({ error: "请求失败" }));
    throw new Error(err.error || `HTTP ${r.status}`);
  }
  return r.json();
}

// --- scene mutate (transform etc.) ---

// 1) 平移
export async function postTranslate({ id, dx, dy }) {
  const r = await fetch(`${API}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, dx, dy }),
  });
  if (!r.ok) throw new Error(`POST /translate ${r.status}`);
  return r.json(); // { ok: true/false }
}

// 2) 旋转（预留，后面会用）
export async function postRotate({ id, theta, cx, cy }) {
  const r = await fetch(`${API}/rotate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, theta, cx, cy }),
  });
  if (!r.ok) throw new Error(`POST /rotate ${r.status}`);
  return r.json(); // { ok: true/false }
}

// 3) 缩放（预留，后面会用）
export async function postScale({ id, sx, sy, cx, cy }) {
  const r = await fetch(`${API}/scale`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, sx, sy, cx, cy }),
  });
  if (!r.ok) throw new Error(`POST /scale ${r.status}`);
  return r.json(); // { ok: true/false }
}

export async function postClipRect(payload) {
  const r = await fetch("/api/v1/clip_rect", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.error || `POST /clip_rect ${r.status}`);
  }
  return r.json();
}

// --- undo / clear ---

export async function postUndo() {
  const r = await fetch(`${API}/undo`, { method: "POST" });
  if (!r.ok) throw new Error(`POST /undo ${r.status}`);
  return r.json(); // undo() 之后服务端返回 flatten_points()
}

export async function clearCanvas() {
  const r = await fetch(`${API}/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!r.ok) throw new Error("Failed to clear canvas");
  return r.json(); // clear() 之后返回新的 flatten_points()
}

export async function postTransformBegin() {
  await fetch(`/api/v1/transform_begin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
}

export async function postTransformEnd() {
  await fetch(`/api/v1/transform_end`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
}
export function attachStyleFields(base) {
  return {
    ...base,
    style: state.lineStyle,     // "solid" / "dash-6-4" ...
    dash_on: state.dashOn,      // 整数像素
    dash_off: state.dashOff,    // 整数像素
  };
}