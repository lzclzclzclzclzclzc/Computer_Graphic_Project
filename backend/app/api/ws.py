# backend/app/api/ws.py
from flask_socketio import emit
from ..extensions import socketio
from ..services.scene_service import get_scene_service
import math

@socketio.on("connect")
def handle_connect():
    print("WebSocket client connected")

@socketio.on("disconnect")
def handle_disconnect():
    print("WebSocket client disconnected")

@socketio.on("subscribe_points")
def handle_subscribe_points():
    svc = get_scene_service()
    try:
        pts = svc.get_points()
        print("[ws] subscribe_points: got", len(pts) if pts is not None else "None", "points")
        emit("points_update", pts)
    except Exception as e:
        print("[ws] subscribe_points ERROR:", repr(e))

# ============================================
# 调试事件（用于确认前端事件是否到达后端）
# ============================================
@socketio.on("debug_test")
def handle_debug_test(data):
    print("[ws] debug_test received:", data)

# ============================================
# 旋转动画
# ============================================
@socketio.on("start_rotation_animation")
def handle_start_rotation_animation(data):
    """
    data:
      {
        "id": "<shape id>",
        "cx": <float>,
        "cy": <float>,
        "speed": <float>  # 弧度/秒
      }
    """
    print("[ws] start_rotation_animation received raw data:", data)

    if not data:
        print("[ws] start_rotation_animation ERROR: data is None or empty")
        emit("start_rotation_animation_ack", {"id": None, "ok": False, "reason": "no_data"})
        return

    shape_id = data.get("id")
    if not shape_id:
        print("[ws] start_rotation_animation ERROR: missing 'id'")
        emit("start_rotation_animation_ack", {"id": None, "ok": False, "reason": "missing_id"})
        return

    try:
        cx = float(data.get("cx", 0))
        cy = float(data.get("cy", 0))
        speed = float(data.get("speed", math.pi / 2))
    except (TypeError, ValueError) as e:
        print("[ws] start_rotation_animation ERROR: invalid numeric field:", e)
        emit("start_rotation_animation_ack", {
            "id": shape_id,
            "ok": False,
            "reason": "invalid_numeric",
        })
        return

    print(
        "[ws] start_rotation_animation parsed:",
        "id=", shape_id, "cx=", cx, "cy=", cy, "speed=", speed
    )

    svc = get_scene_service()
    ok = False
    reason = "ok"

    try:
        # 建议让 SceneService.start_rotation_animation 返回 True/False
        ok = bool(svc.start_rotation_animation(shape_id, cx, cy, speed_rad_per_sec=speed))
        print("[ws] start_rotation_animation dispatched to scene_service, result:", ok)
        if not ok:
            reason = "scene_service_reject"  # 例如 shape 不存在
    except Exception as e:
        print("[ws] start_rotation_animation ERROR in scene_service:", repr(e))
        ok = False
        reason = "exception"

    # 给前端一个确认
    emit("start_rotation_animation_ack", {
        "id": shape_id,
        "ok": ok,
        "reason": reason,
    })

# ============================================
# ⭐⭐ 平移动画
# ============================================
@socketio.on("start_translate_animation")
def handle_start_translate_animation(data):
    """
    data:
      {
        "id": "<shape id>",
        "vx": <float>,   # x 方向速度（像素/秒）
        "vy": <float>    # y 方向速度（像素/秒）
      }
    """
    print("[ws] start_translate_animation received raw data:", data)

    if not data:
        print("[ws] start_translate_animation ERROR: data is None or empty")
        emit("start_translate_animation_ack", {"id": None, "ok": False, "reason": "no_data"})
        return

    shape_id = data.get("id")
    if not shape_id:
        print("[ws] start_translate_animation ERROR: missing 'id'")
        emit("start_translate_animation_ack", {"id": None, "ok": False, "reason": "missing_id"})
        return

    try:
        vx = float(data.get("vx", 0))
        vy = float(data.get("vy", 0))
    except (TypeError, ValueError) as e:
        print("[ws] start_translate_animation ERROR: invalid numeric field:", e)
        emit("start_translate_animation_ack", {
            "id": shape_id,
            "ok": False,
            "reason": "invalid_numeric",
        })
        return

    print(
        "[ws] start_translate_animation parsed:",
        "id=", shape_id, "vx=", vx, "vy=", vy
    )

    svc = get_scene_service()
    ok = False
    reason = "ok"

    try:
        ok = bool(svc.start_translate_animation(shape_id, vx, vy))
        print("[ws] start_translate_animation dispatched to scene_service, result:", ok)
        if not ok:
            reason = "scene_service_reject"
    except Exception as e:
        print("[ws] start_translate_animation ERROR in scene_service:", repr(e))
        ok = False
        reason = "exception"

    emit("start_translate_animation_ack", {
        "id": shape_id,
        "ok": ok,
        "reason": reason,
    })

# ============================================
# 停止动画（通用）
# ============================================
@socketio.on("stop_animation")
def handle_stop_animation():
    print("[ws] stop_animation received")
    svc = get_scene_service()
    ok = True
    reason = "ok"

    try:
        svc.stop_animation()
        print("[ws] stop_animation dispatched to scene_service")
    except Exception as e:
        print("[ws] stop_animation ERROR in scene_service:", repr(e))
        ok = False
        reason = "exception"

    emit("stop_animation_ack", {"ok": ok, "reason": reason})