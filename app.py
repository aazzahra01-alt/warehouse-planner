"""Entry point Flask: application factory."""
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from config import config_by_name
from database import init_db
from routes import register_blueprints
from services.exceptions import ServiceError


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.getenv("APP_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name]())
    app.json.sort_keys = False

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    init_db(app)
    register_blueprints(app)
    _register_error_handlers(app)
    return app


def _register_error_handlers(app: Flask) -> None:
    def json_error(status: int, message: str):
        return jsonify({"status": "error", "message": message}), status

    @app.errorhandler(ServiceError)
    def handle_service_error(exc: ServiceError):
        return jsonify(exc.to_dict()), exc.status_code

    @app.errorhandler(404)
    def not_found(_):
        if request.path.startswith("/api/"):
            return json_error(404, "Endpoint tidak ditemukan.")
        return "Halaman tidak ditemukan.", 404

    @app.errorhandler(413)
    def too_large(_):
        return json_error(413, "Ukuran file melebihi batas 200 MB.")

    @app.errorhandler(500)
    def server_error(_):
        return json_error(500, "Terjadi kesalahan pada server.")


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
