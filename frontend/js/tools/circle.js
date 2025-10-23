import { state } from "../state.js";
import { drawPreviewDot } from "../render.js";
import { postCircle } from "../api.js";


export async function handleClickCircle(x, y, refresh) {
  if (state.points.length < 2) {
    drawPreviewDot(x, y, state.currentColor);
    state.points.push({ x, y });
    return;
  }

  state.points.push({ x, y });
  const [p1, p2, p3] = state.points;

  await postCircle({
    x1: p1.x, y1: p1.y,
    x2: p2.x, y2: p2.y,
    x3: p3.x, y3: p3.y,
    color: state.currentColor,
    width: state.currentWidth,
  });

  state.set({ points: [] });
  await refresh();
}
