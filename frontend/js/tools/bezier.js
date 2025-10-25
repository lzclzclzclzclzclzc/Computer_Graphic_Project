// tools/bezier.js
import { state } from "../state.js";
import { initRender, paintAll, drawPreviewDot } from "../render.js";
import { postBezier } from "../api.js";

export async function handleClickBezier(x, y, button, refresh) {
  if (button === 0) { // 左键：添加控制点
    state.points.push({ x, y });
    drawPreviewDot(x, y, state.currentColor); 
  } else if (button === 2) { // 右键：结束绘制
    if (state.points.length < 2) {
      console.warn("至少需要两个点才能绘制 Bézier 曲线");
      state.set({ points: [] });
      return;
    }

    try {
      await postBezier({
        points: state.points,
        color: state.currentColor,
        width: state.currentWidth,
      });
      state.set({ points: [] });
      await refresh();
    } catch (err) {
      console.error("Bézier 绘制失败：", err);
    }
  }
}
