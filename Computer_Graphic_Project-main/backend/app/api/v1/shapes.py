# backend/app/api/v1/shapes.py
from flask import Blueprint, request, jsonify
from ...domain.scene import Scene
from ...services.scene_service import SceneService

bp = Blueprint("shapes", __name__)
_scene = Scene()
svc = SceneService(_scene)

@bp.post("/lines")
def create_line():
    return jsonify(svc.add_line(request.get_json(force=True)))

@bp.post("/rectangles")
def create_rectangle():
    return jsonify(svc.add_rect(request.get_json(force=True)))

@bp.get("/points")
def get_points():
    return jsonify(svc.get_points())

@bp.get("/lines")
def lines_explain():
    return {"hint": "Use POST /api/v1/lines with JSON {x1,y1,x2,y2}."}

@bp.post("/circles")
def create_circle():
    return jsonify(svc.add_circle(request.get_json(force=True)))

@bp.post("/undo")
def undo():
    return jsonify(svc.undo())