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