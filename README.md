## 安装依赖
```shell
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt
```
## 启动后端服务器
```shell
python wsgi.py
```
访问：http://127.0.0.1:5000/