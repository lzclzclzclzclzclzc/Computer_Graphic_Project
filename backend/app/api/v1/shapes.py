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

def _float(v, default):
    try:
        return float(v)
    except Exception:
        return default


# -----------------------------
# 创建各种图形
# -----------------------------

@bp.post("/lines")
def create_line():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")
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
    width = max(1, _int(data.get("width", 1), 1))

    try:
        result = svc.add_rect(data, color=color, width=width)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.post("/circles")
def create_circle():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")
    width = max(1, _int(data.get("width", 1), 1))

    try:
        result = svc.add_circle(data, color=color, width=width)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.post("/bezier")
def create_bezier():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")
    width = max(1, _int(data.get("width", 1), 1))

    try:
        result = svc.add_bezier(data, color=color, width=width)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.post("/polygons")
def create_polygon():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")
    width = max(1, _int(data.get("width", 1), 1))

    try:
        result = svc.add_polygon(data, color=color, width=width)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400 
    

@bp.post("/bspline")
def create_bspline():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")
    width = max(1, _int(data.get("width", 1), 1))

    try:
        degree = _int(data.get("degree", 3), 3)
        result = svc.add_bspline(data, degree=degree, color=color, width=width)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.post("/arc")
def create_arc():
    data = request.get_json(force=True)
    color = data.get("color", "#ff0000")
    width = max(1, _int(data.get("width", 1), 1))

    try:
        result = svc.add_arc(data, color=color, width=width)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# -----------------------------
# 查询 / 状态
# -----------------------------

@bp.get("/points")
def get_points():
    # 展开整场景为像素点
    return jsonify(svc.get_points())

@bp.get("/lines")
def lines_explain():
    return jsonify({"hint": "POST /api/v1/lines with JSON {x1,y1,x2,y2,color,width}."})

@bp.post("/undo")
def undo():
    return jsonify(svc.undo())

@bp.post("/clear")
def clear_canvas():
    points = svc.clear()
    return jsonify(points)

@bp.get("/scene")
def dump_scene_state():
    """
    可选调试接口，看看当前所有 shape 的几何和 transform。
    有助于前端做选框/控制柄等。
    """
    return jsonify(svc.dump_scene_state())


# -----------------------------
# 变换：平移 / 旋转 / 缩放
# -----------------------------

@bp.post("/translate")
def translate_shape():
    """
    body:
    {
        "id": "<shape id>",
        "dx": <number>,
        "dy": <number>
    }
    """
    data = request.get_json(force=True) or {}
    shape_id = data.get("id")
    dx = _float(data.get("dx", 0), 0.0)
    dy = _float(data.get("dy", 0), 0.0)

    points = svc.translate_shape(shape_id, dx, dy)
    # points 应该是一个数组，比如 [ {x, y, color, id, w}, ... ]
    return jsonify(points)

@bp.post("/rotate")
def rotate_shape():
    """
    期望 body:
    {
        "id": "<shape id>",
        "theta": <radians>,   // 旋转角，弧度
        "cx": <number>,       // 旋转中心x（世界坐标）
        "cy": <number>        // 旋转中心y（世界坐标）
    }
    """
    data = request.get_json(force=True) or {}
    shape_id = data.get("id")
    theta = _float(data.get("theta", 0), 0.0)
    cx = _float(data.get("cx", 0), 0.0)
    cy = _float(data.get("cy", 0), 0.0)

    ok = svc.rotate_shape(shape_id, theta, cx, cy)
    return jsonify({"ok": bool(ok)})

@bp.post("/scale")
def scale_shape():
    """
    期望 body:
    {
        "id": "<shape id>",
        "sx": <number>,       // scaleX
        "sy": <number>,       // scaleY
        "cx": <number>,       // 缩放中心x
        "cy": <number>        // 缩放中心y
    }
    """
    data = request.get_json(force=True) or {}
    shape_id = data.get("id")
    sx = _float(data.get("sx", 1), 1.0)
    sy = _float(data.get("sy", 1), 1.0)
    cx = _float(data.get("cx", 0), 0.0)
    cy = _float(data.get("cy", 0), 0.0)

    ok = svc.scale_shape(shape_id, sx, sy, cx, cy)
    return jsonify({"ok": bool(ok)})
@bp.post("/transform_begin")
def transform_begin():
    svc.begin_transform_session()
    return jsonify({"ok": True})

@bp.post("/transform_end")
def transform_end():
    svc.end_transform_session()
    return jsonify({"ok": True})

# backend/app/shapes.py

@bp.post("/clip_rect")
def clip_rect():
    data = request.get_json(force=True) or {}
    pts = svc.clip_rect(
        data["id"],
        float(data["x1"]),
        float(data["y1"]),
        float(data["x2"]),
        float(data["y2"]),
    )
    return jsonify(pts)

