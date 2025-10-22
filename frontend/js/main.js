const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const API = "/api/v1";

let mode = "line";        // line | rect | move
let points = [];
const pixelSize = 2;

let currentColor = "#ff0000";
const colorEl = document.getElementById("colorPicker");
if (colorEl) {
  colorEl.addEventListener("input", (e) => currentColor = e.target.value);
}

function setActive(id) {
  document.querySelectorAll(".controls button").forEach(btn => btn.classList.remove("active"));
  const el = document.getElementById(id);
  if (el) el.classList.add("active");
}

function drawPreviewDot(x, y, color = "#00c853") {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, pixelSize + 1, pixelSize + 1);
}

let cachedPts = [];
let shapesById = new Map();
let selectedId = null;
let moveStart = null;

async function refresh() {
  try {
    const r = await fetch(`${API}/points`, { cache: "no-store" });
    if (!r.ok) throw new Error(`GET /points ${r.status}`);
    const pts = await r.json();
    cachedPts = pts;

    shapesById = new Map();
    for (const p of pts) {
      if (!p.id) continue;
      const arr = shapesById.get(p.id) || [];
      arr.push(p);
      shapesById.set(p.id, arr);
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const p of pts) {
      ctx.fillStyle = p.color || "red";
      ctx.fillRect(p.x, p.y, pixelSize, pixelSize);
    }

    if (selectedId) highlightShape(selectedId);
  } catch (err) {
    console.error("刷新失败：", err);
  }
}

function highlightShape(id) {
  const pts = shapesById.get(id);
  if (!pts || !pts.length) return;
  for (const p of pts) { // 外圈淡蓝
    ctx.fillStyle = "rgba(33,150,243,0.35)";
    ctx.fillRect(p.x - 1, p.y - 1, pixelSize + 2, pixelSize + 2);
  }
  for (const p of pts) { // 中心原色
    ctx.fillStyle = p.color || "red";
    ctx.fillRect(p.x, p.y, pixelSize, pixelSize);
  }
}

document.getElementById("lineBtn").onclick = () => { mode = "line"; setActive("lineBtn"); selectedId = null; moveStart = null; };
document.getElementById("rectBtn").onclick = () => { mode = "rect"; setActive("rectBtn"); selectedId = null; moveStart = null; };
document.getElementById("moveBtn").onclick = () => { mode = "move"; setActive("moveBtn"); selectedId = null; moveStart = null; };

document.getElementById("undoBtn").onclick = async () => {
  try {
    const r = await fetch(`${API}/undo`, { method: "POST" });
    if (!r.ok) throw new Error(`POST /undo ${r.status}`);
    await refresh();
  } catch (err) {
    console.error("撤销失败：", err);
  } finally {
    points = [];
    selectedId = null;
    moveStart = null;
  }
};

function dist(x1, y1, x2, y2) { return Math.hypot(x1 - x2, y1 - y2); }

function minDistToPointCloud(points, x, y, sampleStep = 1) {
  let best = Infinity;
  for (let i = 0; i < points.length; i += sampleStep) {
    const p = points[i];
    const d = dist(p.x, p.y, x, y);
    if (d < best) best = d;
    if (best === 0) break;
  }
  return best;
}

function pickShapeByPoint(x, y, threshold = 12) {
  let winnerId = null, best = Infinity;
  for (const [id, pts] of shapesById.entries()) {
    const d = minDistToPointCloud(pts, x, y, 1); // 需要更快可用 2 或 3
    if (d < best) { best = d; winnerId = id; }
  }
  if (best <= threshold) return { id: winnerId, dist: best };
  return null;
}

canvas.addEventListener("click", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);

  if (mode === "move") {
    if (!selectedId) {
      const hit = pickShapeByPoint(x, y, 12);
      if (!hit) { drawPreviewDot(x, y, "#ffab00"); return; }
      selectedId = hit.id;
      moveStart = { x, y };
      highlightShape(selectedId);
      return;
    }
    const dx = x - moveStart.x;
    const dy = y - moveStart.y;
    try {
      const r = await fetch(`${API}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: selectedId, dx, dy })
      });
      if (!r.ok) throw new Error(`POST /move ${r.status}`);
    } catch (err) {
      console.error("移动失败：", err);
      alert("移动失败：检查 /api/v1/move 与点集中 id 字段。");
    } finally {
      selectedId = null;
      moveStart = null;
      await refresh();
    }
    return;
  }

  if (points.length === 0) {
    drawPreviewDot(x, y, currentColor);
    points.push({ x, y });
    return;
  }

  points.push({ x, y });
  const payload = {
    x1: points[0].x, y1: points[0].y,
    x2: points[1].x, y2: points[1].y,
    color: currentColor
  };
  const endpoint = (mode === "line") ? "lines" : "rectangles";

  try {
    const r = await fetch(`${API}/${endpoint}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!r.ok) {
      const text = await r.text().catch(() => "");
      throw new Error(`POST /${endpoint} ${r.status} ${text}`);
    }
  } catch (err) {
    console.error("绘制失败：", err);
    alert("绘制失败：检查后端是否运行/路由是否匹配。");
  } finally {
    points = [];
    await refresh();
  }
});

// 启动刷新
refresh();