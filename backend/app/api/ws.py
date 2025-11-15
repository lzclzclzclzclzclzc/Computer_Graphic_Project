from flask_socketio import emit
from ..extensions import socketio
from ..services.scene_service import get_scene_service


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
    emit("points_update", pts)