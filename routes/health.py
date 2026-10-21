from flask import Blueprint, jsonify

from services.health_service import check_database

health_bp = Blueprint("health", __name__)


@health_bp.get("/healthcheck")
def healthcheck():
    ok, error = check_database()
    if ok:
        return jsonify({"status": "ok", "database": "connected"}), 200
    return jsonify({"status": "error", "database": "disconnected", "detail": error}), 503
