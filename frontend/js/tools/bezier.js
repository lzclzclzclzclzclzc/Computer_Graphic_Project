import { state } from "../state.js";
import { drawPreviewDot } from "../render.js";
import { postBezier } from "../api.js";

/**
 * 点击 Bézier 曲线画布逻辑
 * 1. 点击时显示预览点
 * 2. 收集控制点
 * 3. 点击 4 个点后发送给后端
 */
export async function handleClickBezier(x, y, refresh) {
  // 绘制预览点
  drawPreviewDot(x, y, state.currentColor);
  state.points.push({ x, y });

  // 假设四阶 Bézier（4 个控制点）完成绘制
  if (state.points.length < 4) return;

  const pts = state.points;

  try {
    await postBezier({
      points: pts,
      color: state.currentColor,
      width: state.currentWidth,
    });
    // 清空临时点
    state.set({ points: [] });
    // 刷新画布
    await refresh();
  } catch (e) {
    console.error("Bézier 绘制失败：", e);
  }
}
