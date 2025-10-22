const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const API = "/api/v1";          // 相对路径，避免跨域/端口问题
let mode = "line";               // "line" | "rect"
let points = [];                 // [起点?, 终点?]
const pixelSize = 2;             // 预览/绘制像素大小（Retina 上更明显）

// —— 移动模式用的状态 —— //
let selectedId = null;     // 被选中的线的 id
let moveStart = null;      // 第一次点击位置（用于计算 dx, dy）
let cachedPts = [];        // 最近一次 refresh 缓存的点，避免重复拉取

let currentColor = "#ff0000"; // 默认颜色
document.getElementById("colorPicker").addEventListener("input", (e) => {
  currentColor = e.target.value;
});//线条颜色监听

async function refresh() {
  try {
    const r = await fetch(`${API}/points`);
    if (!r.ok) throw new Error(`GET /points ${r.status}`);
    const pts = await r.json();
    cachedPts = pts;                    // ✅ 缓存起来
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    pts.forEach(p => {
      ctx.fillStyle = p.color || "red";
      ctx.fillRect(p.x, p.y, pixelSize, pixelSize);
    });

    // 如果当前选中某条线，可以加一个小预览标记（可选）
    if (selectedId && moveStart) {
      drawPreviewDot(moveStart.x, moveStart.y, "#2196f3");
    }
  } catch (err) {
    console.error("刷新失败：", err);
  }
}

function drawPreviewDot(x, y, color = "#00c853") {
  ctx.fillStyle = color;
  ctx.fillRect(x, y, pixelSize + 1, pixelSize + 1);
}


canvas.addEventListener("click", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);

  // —— 移动模式 —— //
  if (mode === "move") {
    // 第一次点击：命中测试 -> 选中一条线
    if (!selectedId) {
      const hit = pickClosestPoint(x, y, cachedPts, 4);
      if (!hit) {
        // 没点到任何线，轻提示（可选）
        drawPreviewDot(x, y, "#ffab00"); // 琥珀色小点提示没选中
        return;
      }
      selectedId = hit.id;
      moveStart = { x, y };
      drawPreviewDot(x, y, "#2196f3"); // 选中点预览（蓝色）
      return;
    }

    // 第二次点击：计算位移并提交移动
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
      alert("移动失败：请检查后端 /api/v1/move 接口。");
    } finally {
      selectedId = null;
      moveStart = null;
      await refresh();
    }
    return;
  }

  // —— 非移动模式：你的原有绘图逻辑 —— //
  if (points.length === 0) {
    // 预览第一点：用当前颜色
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
  const endpoint = mode === "line" ? "lines" : "rectangles";

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
    alert("请求失败，请检查后端是否在 127.0.0.1:5000 运行，或接口路径是否正确。");
  } finally {
    points = [];
    await refresh();
  }
});


document.getElementById("undoBtn").onclick = async () => {
  try {
    const r = await fetch(`${API}/undo`, { method: "POST" });
    if (!r.ok) throw new Error(`POST /undo ${r.status}`);
    await refresh();
  } catch (err) {
    console.error("撤销失败：", err);
  } finally {
    points = [];
  }
};

document.getElementById("lineBtn").onclick = () => {
  mode = "line";
  setActive("lineBtn");
};

document.getElementById("rectBtn").onclick = () => {
  mode = "rect";
  setActive("rectBtn");
};

document.getElementById("moveBtn").onclick = () => {
  mode = "move";
  setActive("moveBtn");
  // 进入移动模式时清理一次临时状态
  selectedId = null;
  moveStart = null;
};

function setActive(id) {
  document.querySelectorAll(".controls button").forEach(btn => btn.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

function pickClosestPoint(x, y, pts, threshold = 99999) {
  let best = null, bestDist = Infinity;
  for (const p of pts) {
    const dx = p.x - x, dy = p.y - y;
    const d = Math.hypot(dx, dy);
    if (d < bestDist && d <= threshold) {
      bestDist = d;
      best = p;
    }
  }
  return best;
}

refresh();