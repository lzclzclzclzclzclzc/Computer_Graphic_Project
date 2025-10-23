import { state } from "../state.js";
import { pickShapeByPoint } from "../picker.js";
import { drawPreviewDot, highlightShape } from "../render.js";
import { postMove } from "../api.js";

export async function handleClickMove(x, y, refresh) {
  if (!state.selectedId) {
    const hit = pickShapeByPoint(x, y, 12);
    if (!hit) { drawPreviewDot(x, y, "#ffab00"); return; }
    state.set({ selectedId: hit.id, moveStart: { x, y } });
    highlightShape(state.selectedId);
    return;
  }
  const dx = x - state.moveStart.x;
  const dy = y - state.moveStart.y;
  await postMove({ id: state.selectedId, dx, dy });
  state.set({ selectedId: null, moveStart: null });
  await refresh();
}