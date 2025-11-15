# backend/app/extensions.py
from flask_cors import CORS
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")  # 允许跨域访问 WebSocket

def init_extensions(app):

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    socketio.init_app(app)