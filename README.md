## 安装依赖
```shell
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt
```
## 启动后端服务器
```shell
python backend/wsgi.py
```
访问：http://127.0.0.1:5050/

## 待实现功能
- websocket 改写前端，实现动画函数
    - 生成圆形，运动轨迹为圆形
    - 生成直线，绕端点旋转
- mcp server 增加填充功能

## 测试动画函数
	1.	在画布上画一个图形
	2.	打开 http://127.0.0.1:5050/api/v1/scene
	3.	复制 id
	4.	浏览器 Console 依次输入：
```js
// 订阅一次
socket.emit("subscribe_points");

// 平移
socket.emit("start_translate_animation", {
  id: "你的id",
  vx: 100,
  vy: 0
});

// 停止
socket.emit("stop_animation");

// 旋转
socket.emit("start_rotation_animation", {
  id: "你的id",
  cx: 400,
  cy: 300,
  speed: Math.PI / 2
});

// 再停
socket.emit("stop_animation");
```