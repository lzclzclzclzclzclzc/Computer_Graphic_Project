# backend/wsgi.py
from app import create_app
app = create_app()

@app.route("/")
def index():
    return app.send_static_file("index.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)