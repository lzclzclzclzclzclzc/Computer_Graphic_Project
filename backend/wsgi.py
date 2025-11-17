# backend/wsgi.py
from app import create_app
from app.extensions import socketio

# 👇 关键：导入 app.api.ws，让所有 @socketio.on 事件真正注册
import app.api.ws  # 只要 import，不需要用变量

app = create_app()


@app.route("/")
def index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", port=5050, debug=True)