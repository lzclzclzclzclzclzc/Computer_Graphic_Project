# backend/app/extensions.py
from flask_cors import CORS

def init_extensions(app):

    CORS(app, resources={r"/api/*": {"origins": "*"}})