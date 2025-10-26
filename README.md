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
访问：http://127.0.0.1:5000/

## 待实现功能
1. 任意多边形绘制
2. 扫描线填充
3. 实现二维直线段裁剪的 Cohen-Sutherland 裁剪算法或中点分割裁剪算法。
4. 放缩旋转
### 挑战问题
1. 圆弧段
2. 裁剪窗口为任意凸多边形
3. 在两个图形的轮廓上指定对接点，通过几何变换，将两个图形在对接点处拼接。
