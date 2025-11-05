// tools/bspline.js
import { state } from "../state.js";
import { initRender, paintAll, drawPreviewDot } from "../render.js";
import { postBSpline } from "../api.js";

export async function handleClickBSpline(x, y, button, refresh) {
  if (button === 0) {
    // 左键：添加控制点
    state.points.push({ x, y });
    drawPreviewDot(x, y, state.currentColor);

  } else if (button === 2) {
    // 右键：结束绘制
    if (state.points.length < 4) {
      alert("B样条至少需要 4 个控制点");
      state.set({ points: [] });
      return;
    }

    // 提示用户输入阶数或次数
    const degreeStr = prompt("请输入B样条的次数（默认 3，对应四阶）", "3");
    const degree = parseInt(degreeStr) || 3;

    try {
      await postBSpline({
        points: state.points,
        degree: degree,
        color: state.currentColor,
        width: state.currentWidth,
      });

      state.set({ points: [] });
      await refresh();
    } catch (err) {
      console.error("B样条绘制失败：", err);
    }
  }
}
