from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

ALL_POINTS = []

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

    ALL_POINTS.extend(new_points)
    return jsonify(ALL_POINTS)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
