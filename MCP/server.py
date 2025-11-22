from fastmcp import FastMCP
import requests
import math
import time
import socketio

# MCP 服务
mcp = FastMCP(name="Painter", host="127.0.0.1", port=12345)

# Flask 后端地址
BACKEND_HTTP_URL = "http://127.0.0.1:5050"
API_PREFIX = "/api/v1"
BACKEND_URL = BACKEND_HTTP_URL + API_PREFIX
BACKEND_WS_URL = BACKEND_HTTP_URL  # 如果 WS 单独走别的地址/路径，在这里改


# -----------------------------
# 工具函数：调用 Flask 绘图接口
# -----------------------------

@mcp.tool
def draw_line(x1: float, y1: float, x2: float, y2: float, color: str = "#ff0000", width: int = 1):
    """
    画一条直线
    参数：
        x1, y1: 起点坐标
        x2, y2: 终点坐标
        color: 颜色（默认红色）
        width: 线宽
    """
    payload = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "color": color, "width": width}
    resp = requests.post(f"{BACKEND_URL}/lines", json=payload)
    if resp.status_code != 201:
        return {"error": resp.text}
    return resp.json()


@mcp.tool
def draw_circle(cx: float, cy: float, r: float, color: str = "#ff0000", width: int = 1):
    """
    画一个圆
    参数:
        cx, cy: 圆心坐标
        r: 半径
        color: 颜色（默认红色）
        width: 线宽
    """
    x1, y1 = cx + r, cy
    x2, y2 = cx, cy + r
    x3, y3 = cx - r, cy

    payload = {
        "x1": x1, "y1": y1,
        "x2": x2, "y2": y2,
        "x3": x3, "y3": y3,
        "color": color,
        "width": width
    }

    resp = requests.post(f"{BACKEND_URL}/circles", json=payload)
    if resp.status_code != 201:
        return {"error": resp.text}

    return resp.json()


@mcp.tool
def draw_arc(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, color: str = "#ff0000", width: int = 1):
    """
    画一个圆弧段
    参数:
        x1, y1: 起点坐标
        x2, y2: 圆弧经过点坐标
        x3, y3: 终点坐标
        color: 颜色（默认红色）
        width: 线宽
    """
    payload = {
        "x1": x1, "y1": y1,
        "x2": x2, "y2": y2,
        "x3": x3, "y3": y3,
        "color": color,
        "width": width
    }

    resp = requests.post(f"{BACKEND_URL}/arc", json=payload)
    if resp.status_code != 201:
        return {"error": resp.text}

    return resp.json()


@mcp.tool
def draw_bezier(x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, color: str = "#ff0000", width: int = 1):
    """
    画一个二阶贝塞尔曲线
    参数:
        x1, y1: 起点坐标
        x2, y2: 控制点坐标
        x3, y3: 终点坐标
        color: 颜色（默认红色）
        width: 线宽
    """
    control_points = [
        {"x": x1, "y": y1},
        {"x": x2, "y": y2},
        {"x": x3, "y": y3}
    ]

    payload = {
        "points": control_points,
        "color": color,
        "width": width
    }

    resp = requests.post(f"{BACKEND_URL}/bezier", json=payload)
    if resp.status_code != 201:
        return {"error": resp.text}

    return resp.json()


@mcp.tool
def draw_rectangle(x1: float, y1: float, x2: float, y2: float, color: str = "#ff0000", width: int = 1):
    """
    画一个矩形
    参数:
        x1, y1: 左上角顶点坐标
        x2, y2: 右下角顶点坐标
        color: 颜色（默认红色）
        width: 线宽
    """
    payload = {
        "x1": x1, "y1": y1,
        "x2": x2, "y2": y2,
        "color": color,
        "width": width
    }

    resp = requests.post(f"{BACKEND_URL}/rectangles", json=payload)
    if resp.status_code != 201:
        return {"error": resp.text}

    return resp.json()


@mcp.tool
def clear_canvas():
    """
    清空画布
    """
    url = f"{BACKEND_URL}/clear"
    r = requests.post(url)
    if r.status_code != 200:
        return {"error": r.text}
    return r.json()


@mcp.tool
def draw_and_rotate_circle(cx: float, cy: float, r: float, line_color: str = "#ff0000", width: int = 2) -> str:
    """
    画一个圆形，并立即让它围绕画布中心(400, 300)开始旋转。

    参数:
        cx, cy: 圆心坐标 (例如: 400, 300)
        r: 半径 (例如: 50)
        line_color: 线条颜色 (默认 "#ff0000")
        width: 线宽 (默认 2)
    """

    # 1. 计算三点坐标
    x1, y1 = cx + r, cy
    x2, y2 = cx, cy + r
    x3, y3 = cx - r, cy

    # 2. 发送 HTTP 请求创建圆形
    payload = {
        "x1": x1, "y1": y1,
        "x2": x2, "y2": y2,
        "x3": x3, "y3": y3,
        "color": line_color,
        "width": width
    }

    try:
        create_resp = requests.post(f"{BACKEND_URL}/circles", json=payload)
        if create_resp.status_code != 201:
            return f"创建圆形失败: {create_resp.text}"
    except Exception as e:
        return f"连接后端失败: {str(e)}"

    # 3. 获取场景数据并查找 ID
    try:
        scene_resp = requests.get(f"{BACKEND_URL}/scene")
        if scene_resp.status_code != 200:
            return f"获取场景数据失败: {scene_resp.text}"

        scene_data = scene_resp.json()
    except Exception as e:
        return f"解析场景数据失败: {str(e)}"

    target_id = None
    epsilon = 0.01

    shapes = scene_data.get("shapes", [])
    for shape in reversed(shapes):
        if shape.get("type") != "Circle":
            continue

        geo = shape.get("geometry", {})

        match_x1 = abs(geo.get("x1", 0) - x1) < epsilon
        match_y1 = abs(geo.get("y1", 0) - y1) < epsilon
        match_x2 = abs(geo.get("x2", 0) - x2) < epsilon
        match_y2 = abs(geo.get("y2", 0) - y2) < epsilon
        match_x3 = abs(geo.get("x3", 0) - x3) < epsilon
        match_y3 = abs(geo.get("y3", 0) - y3) < epsilon

        if match_x1 and match_y1 and match_x2 and match_y2 and match_x3 and match_y3:
            target_id = shape.get("id")
            break

    if not target_id:
        return "圆形创建成功，但在场景中未找到对应的 ID，无法执行动画。"

    # 4. 通过 WebSocket 发送旋转指令
    try:
        sio = socketio.Client()
        sio.connect(BACKEND_WS_URL)

        animation_payload = {
            "id": target_id,
            "cx": 400,          # 旋转中心 X
            "cy": 300,          # 旋转中心 Y
            "speed": math.pi / 2  # 旋转角速度
        }

        sio.emit("start_rotation_animation", animation_payload)

        time.sleep(0.1)
        sio.disconnect()

        return f"成功！已创建圆形 (ID: {target_id}) 并开始旋转动画。"

    except Exception as e:
        return f"圆形已创建 (ID: {target_id})，但发送 WebSocket 动画指令失败: {str(e)}"


# -----------------------------
# 主入口
# -----------------------------
def main():
    print("MCP Painter Server running at http://127.0.0.1:12345")
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()