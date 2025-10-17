from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 将所有直线按条保存为列表的栈，每条直线为一个点列表
LINES = []

def flatten_lines():
    pts = []
    for line in LINES:
        pts.extend(line)
    return pts

def bresenham(x1, y1, x2, y2):
    points = []

    x = int(x1)
    y = int(y1)
    x2 = int(x2)
    y2 = int(y2)

    dx = abs(x2 - x)
    dy = abs(y2 - y)
    sx = 1 if x < x2 else -1
    sy = 1 if y < y2 else -1
    err = dx - dy

    while True:
        points.append({"x": x, "y": y})
        if x == x2 and y == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy

    return points

# ------------------ Flask 路由 ------------------
@app.route("/bresenham", methods=["POST"])
def get_points():
    data = request.json
    x1 = int(data["x1"])
    y1 = int(data["y1"])
    x2 = int(data["x2"])
    y2 = int(data["y2"])

    new_points = bresenham(x1, y1, x2, y2)

    # 将整条直线作为一个 list 入栈
    LINES.append(new_points)
    # 返回所有直线的扁平点列表，供前端一次性绘制
    return jsonify(flatten_lines())

# 返回当前所有直线的扁平点列表
@app.route("/lines", methods=["GET"])
def get_all_lines():
    return jsonify(flatten_lines())

# 撤销（弹出）最后一条直线，返回更新后的扁平点列表
@app.route("/undo", methods=["POST"])
def undo():
    if LINES:
        LINES.pop()
    return jsonify(flatten_lines())

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
