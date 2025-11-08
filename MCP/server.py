from fastmcp import FastMCP
import requests

# MCP 服务
mcp = FastMCP(name="Painter", host="127.0.0.1", port=12345)

# Flask 后端地址
BACKEND_URL = "http://127.0.0.1:5000/api/v1"


# -----------------------------
# 工具函数：调用 Flask 绘图接口
# -----------------------------

@mcp.tool
def draw_line(x1: float, y1: float, x2: float, y2: float, color: str = "#00ff00", width: int = 1):
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
    return r.json()


# -----------------------------
# 主入口
# -----------------------------
def main():
    print("MCP Painter Server running at http://127.0.0.1:12345")
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
