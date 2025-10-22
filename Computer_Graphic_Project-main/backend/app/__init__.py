# backend/app/__init__.py
from flask import Flask
from .extensions import init_extensions
from .api.v1.shapes import bp as shapes_bp

def create_app():
    app = Flask(__name__, static_folder="../../", static_url_path="")
    init_extensions(app)
    app.register_blueprint(shapes_bp, url_prefix="/api/v1")
    return app