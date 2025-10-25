const API = "/api/v1";

export async function getPoints() {
  const r = await fetch(`${API}/points`, { cache: "no-store" });
  if (!r.ok) throw new Error(`GET /points ${r.status}`);
  return r.json();
}
export async function postLine(payload) {
  const r = await fetch(`${API}/lines`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!r.ok) throw new Error(`POST /lines ${r.status}`);
}
export async function postRect(payload) {
  const r = await fetch(`${API}/rectangles`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!r.ok) throw new Error(`POST /rectangles ${r.status}`);
}
// 其他导出函数并存于同文件
export async function postCircle(payload) {
  const res = await fetch("/api/v1/circles", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "请求失败" }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function postMove({ id, dx, dy }) {
  const r = await fetch(`${API}/move`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id, dx, dy })
  });
  if (!r.ok) throw new Error(`POST /move ${r.status}`);
}

export async function postUndo() {
  const r = await fetch(`${API}/undo`, { method: "POST" });
  if (!r.ok) throw new Error(`POST /undo ${r.status}`);
}

// 清空画布
export async function clearCanvas() {
  const response = await fetch(`${API}/clear`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    }
  });
  if (!response.ok) {
    throw new Error("Failed to clear canvas");
  }
  return response.json();
}
