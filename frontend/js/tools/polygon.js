// frontend/tools/polygon.js
import { state } from "../state.js";
import { drawPreviewDot } from "../render.js";
import { postPolygon } from "../api.js";

export async function handleClickPolygon(x, y, button, refresh) {
  // 左键：添加参考点
  if (button === 0) {
    drawPreviewDot(x, y, state.currentColor);
    state.points.push({ x, y });
    return;
  }
  
  // 右键：闭合多边形
  if (button === 2) {
    if (state.points.length < 3) {
      alert("至少需要三个点才能构成多边形！");
      return;
    }

    const payload = {
      points: state.points,
      color: state.currentColor,
      width: state.currentWidth,
    };

    try {
      await postPolygon(payload);
      state.set({ points: [] }); // 清空控制点
      await refresh();
    } catch (err) {
      console.error("提交多边形失败：", err);
      alert("绘制多边形失败，请检查控制台错误。");
    }
  }
}
