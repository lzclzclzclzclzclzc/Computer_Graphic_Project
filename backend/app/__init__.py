from flask import Flask
from .extensions import init_extensions
from .api.v1.shapes import bp as shapes_bp
from pathlib import Path

def create_app():
    root = Path(__file__).resolve().parents[1].parent   # .../Painting
    frontend = root / "frontend"

    app = Flask(
        __name__,
        static_folder=str(frontend),
        static_url_path=""
    )

    init_extensions(app)
    app.register_blueprint(shapes_bp, url_prefix="/api/v1")
    return app