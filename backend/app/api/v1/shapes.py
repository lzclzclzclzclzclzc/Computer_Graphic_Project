from flask import Blueprint, request, jsonify
from ...domain.scene import Scene
from ...services.scene_service import SceneService

bp = Blueprint("shapes", __name__)
_scene = Scene()
svc = SceneService(_scene)

@bp.post("/lines")
def create_line():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")  # 默认红色
    return jsonify(svc.add_line(data, color=color))

@bp.post("/rectangles")
def create_rectangle():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")
    return jsonify(svc.add_rect(data, color=color))

@bp.get("/points")
def get_points():
    return jsonify(svc.get_points())

@bp.get("/lines")
def lines_explain():
    return {"hint": "Use POST /api/v1/lines with JSON {x1,y1,x2,y2,color}."}

@bp.post("/undo")
def undo():
    return jsonify(svc.undo())

@bp.post("/move")
def move_shape():
    data = request.get_json(force=True)
    return jsonify(svc.move_shape(data))