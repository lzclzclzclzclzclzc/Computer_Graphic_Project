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
    pts = svc.get_points()
    print("[ws] subscribe_points")
    emit("points_update", pts)

# ============================================
# 调试事件（用于确认前端事件是否到达后端）
# ============================================
@socketio.on("debug_test")
def handle_debug_test(data):
    print("[ws] debug_test received:", data)

# ============================================
# 旋转动画（你已经有了）
# ============================================
@socketio.on("start_rotation_animation")
def handle_start_rotation_animation(data):
    svc = get_scene_service()
    shape_id = data.get("id")
    cx = float(data.get("cx", 0))
    cy = float(data.get("cy", 0))
    speed = float(data.get("speed", math.pi / 2))

    print("[ws] start_rotation_animation:", shape_id, cx, cy, speed)
    svc.start_rotation_animation(shape_id, cx, cy, speed_rad_per_sec=speed)

# ============================================
# ⭐⭐ 平移动画：新增
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
    svc = get_scene_service()
    shape_id = data.get("id")

    vx = float(data.get("vx", 0))
    vy = float(data.get("vy", 0))

    print("[ws] start_translate_animation:", shape_id, vx, vy)
    svc.start_translate_animation(shape_id, vx, vy)

# ============================================
# 停止动画（通用）
# ============================================
@socketio.on("stop_animation")
def handle_stop_animation():
    print("[ws] stop_animation")
    svc = get_scene_service()
    svc.stop_animation()