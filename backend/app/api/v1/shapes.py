from flask import Blueprint, request, jsonify
from ...domain.scene import Scene
from ...services.scene_service import SceneService

bp = Blueprint("shapes", __name__, url_prefix="/api/v1")
_scene = Scene()
svc = SceneService(_scene)

def _int(v, default):
    try:
        return int(v)
    except Exception:
        return default

@bp.post("/lines")
def create_line():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")  # 默认红色
    width = max(1, _int(data.get("width", 1), 1))
    try:
        result = svc.add_line(data, color=color, width=width)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.post("/rectangles")
def create_rectangle():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")
    width = max(1, _int(data.get("width", 1), 1))  # <- 新增：接 width
    try:
        result = svc.add_rect(data, color=color, width=width)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.get("/points")
def get_points():
    return jsonify(svc.get_points())

@bp.get("/lines")
def lines_explain():
    return jsonify({"hint": "POST /api/v1/lines with JSON {x1,y1,x2,y2,color,width}."})

@bp.post("/undo")
def undo():
    return jsonify(svc.undo())

@bp.post("/move")
def move_shape():
    data = request.get_json(force=True) or {}
    ok = svc.move_shape(data)
    return jsonify({"ok": bool(ok)})