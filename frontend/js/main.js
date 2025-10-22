const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const API = "/api/v1";          // 相对路径，避免跨域/端口问题
let mode = "line";               // "line" | "rect"
let points = [];                 // [起点?, 终点?]
const pixelSize = 2;             // 预览/绘制像素大小（Retina 上更明显）

let currentColor = "#ff0000"; // 默认颜色
document.getElementById("colorPicker").addEventListener("input", (e) => {
  currentColor = e.target.value;
});//线条颜色监听

async function refresh() {
  try {
    const r = await fetch(`${API}/points`);
    if (!r.ok) throw new Error(`GET /points ${r.status}`);
    const pts = await r.json();
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    pts.forEach(p => {
      ctx.fillStyle = p.color || "red"; // 固定兜底，不回退到 currentColor
      ctx.fillRect(p.x, p.y, pixelSize, pixelSize);
    });
  } catch (err) {
    console.error("刷新失败：", err);
  }
}

function drawPreviewDot(x, y, color = "#00c853") {
  ctx.fillStyle = currentColor;
  ctx.fillRect(x, y, pixelSize + 1, pixelSize + 1);
}

canvas.addEventListener("click", async (e) => {
  const rect = canvas.getBoundingClientRect();
  const x = Math.round(e.clientX - rect.left);
  const y = Math.round(e.clientY - rect.top);

  if (points.length === 0) {
    drawPreviewDot(x, y, "#00c853");
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

function setActive(id) {
  document.querySelectorAll(".controls button").forEach(btn => btn.classList.remove("active"));
  document.getElementById(id).classList.add("active");
}

refresh();