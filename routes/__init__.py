from flask import Flask
from routes.main import main_bp
from routes.health import health_bp
from routes.sku import sku_bp
from routes.inbound import inbound_bp

def register_blueprints(app: Flask) -> None:
    app.register_blueprint(main_bp)
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(sku_bp, url_prefix="/api")
    app.register_blueprint(inbound_bp, url_prefix="/api")