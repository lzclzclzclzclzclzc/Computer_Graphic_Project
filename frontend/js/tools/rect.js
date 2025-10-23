import { state } from "../state.js";
import { drawPreviewDot } from "../render.js";
import { postRect } from "../api.js";

export async function handleClickRect(x, y, refresh) {
  if (state.points.length === 0) {
    drawPreviewDot(x, y, state.currentColor);
    state.points.push({ x, y });
    return;
  }
  state.points.push({ x, y });
  const [p1, p2] = state.points;
  await postRect({ x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y, color: state.currentColor });
  state.set({ points: [] });
  await refresh();
}