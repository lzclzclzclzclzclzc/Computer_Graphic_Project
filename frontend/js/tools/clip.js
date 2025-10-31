// frontend/js/tools/clip.js
import { state } from "../state.js";
import { drawPreviewDot } from "../render.js";
import { postClipRect } from "../api.js";
import { pickShapeByPoint } from "../picker.js";

export async function handleClickClip(x, y, button, refresh) {
  // 1. 如果此时还没有选中的图形，先尝试以当前点选一下
  if (!state.selectedId) {
    const hit = pickShapeByPoint(x, y, 14);
    if (hit) {
      state.set({ selectedId: hit.id });
    } else {
      alert("请先在“移动”模式点一下要裁剪的图形，再切到裁剪模式。");
      return;
    }
  }

  // 2. 第一次点：记住矩形的第一个角
  if (state.points.length === 0) {
    drawPreviewDot(x, y, "#00c853");
    state.points.push({ x, y });
    return;
  }

  // 3. 第二次点：发送裁剪
  state.points.push({ x, y });
  const [p1, p2] = state.points;

  await postClipRect({
    id: state.selectedId,
    x1: p1.x, y1: p1.y,
    x2: p2.x, y2: p2.y,
  });

  // 清临时点，保持还是 clip 模式
  state.set({ points: state.points = [] });
  await refresh();
}
