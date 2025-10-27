import { state } from "../state.js";
import { postTranslate, getPoints } from "../api.js";
import { paintAll } from "../render.js";
import { rebuildIndex } from "../picker.js";

export function handleClickMove(x, y) {
  const hitId = pickShapeAt(x, y, state.cachedPts);
  state.set({ selectedId: hitId || null });
}

export function beginMoveDrag(canvas, x0, y0) {
  console.log("[beginMoveDrag] start", { x0, y0, selectedId_before: state.selectedId });

  // 如果当前没有已选中的，就用起点去捡一个
  if (!state.selectedId) {
    const picked = pickShapeAt(x0, y0, state.cachedPts);
    console.log("[beginMoveDrag] picked =", picked, "cachedPts len=", state.cachedPts.length);
    state.set({ selectedId: picked || null });
  }

  console.log("[beginMoveDrag] selectedId after pick:", state.selectedId);

  if (!state.selectedId) {
    console.log("[beginMoveDrag] no selectedId -> abort drag");
    return;
  }

  // 记录拖拽起点
  state.set({ moveStart: { x: x0, y: y0 } });
  console.log("[beginMoveDrag] drag starts with moveStart=", state.moveStart);

  function onMouseMove(ev) {
    console.log("[onMouseMove fired raw]", ev.clientX, ev.clientY);

    if (!state.moveStart || !state.selectedId) return;

    const rect2 = canvas.getBoundingClientRect();
    const xNow = Math.round(ev.clientX - rect2.left);
    const yNow = Math.round(ev.clientY - rect2.top);

    const dx = xNow - state.moveStart.x;
    const dy = yNow - state.moveStart.y;

    console.log("[onMouseMove] fired ▸ {dx:", dx, ", dy:", dy, "}");

    if (dx === 0 && dy === 0) return;

    postTranslate({ id: state.selectedId, dx, dy })
      .then((r) => {
        // 现在后端 /translate 应该直接返回 flatten_points() 数组
        // 兜底一下：如果不是数组，就主动拉 points
        if (Array.isArray(r)) {
          return r;
        }
        return getPoints();
      })
      .then((pts) => {
        console.log("[onMouseMove] got points:", pts && pts.length);

        // 更新画布状态：这一步会触发 onChange -> paintAll
        state.set({
          cachedPts: pts,
          moveStart: { x: xNow, y: yNow }, // 下次增量基于当前位置
        });

        // 我们也同步 picker 的索引，保证命中检测是最新的
        rebuildIndex();
      })
      .catch(err => {
        console.error("postTranslate failed:", err);
      });
  }

  function onMouseUp() {
    console.log("[onMouseUp] end drag");

    // 拖拽最终结束后，我们做一次彻底同步：
    // 1. 向后端拿一次最新点阵（保证没有旧影子）
    // 2. 更新 cachedPts / moveStart
    // 3. 重建索引
    // 4. 强制重画一次
    getPoints()
      .then((finalPts) => {
        state.set({
          cachedPts: finalPts,
          moveStart: null,
        });
        rebuildIndex();
        paintAll();
      })
      .catch((err) => {
        console.error("刷新失败 after drag:", err);
        // 即使失败也要把 moveStart 清掉，不然下次拖拽状态会乱
        state.set({ moveStart: null });
      });

    // 解绑全局监听
    document.removeEventListener("mousemove", onMouseMove);
    document.removeEventListener("mouseup", onMouseUp);
  }

  // 绑定全局监听，开始拖拽
  document.addEventListener("mousemove", onMouseMove);
  document.addEventListener("mouseup", onMouseUp);
  console.log("[beginMoveDrag] mousemove bound ✅");
}

// 点击附近像素 -> shape id
function pickShapeAt(x, y, pts) {
  if (!pts || pts.length === 0) return null;

  // 精准匹配
  const exact = pts.find(p => p.x === x && p.y === y);
  if (exact) return exact.id;

  // 模糊半径匹配
  const R = 4;
  for (const p of pts) {
    const dx = p.x - x;
    const dy = p.y - y;
    if (dx * dx + dy * dy <= R * R) {
      return p.id;
    }
  }
  return null;
}