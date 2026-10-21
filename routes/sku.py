from flask import Blueprint, jsonify, request

from services import sku_service
from services.exceptions import ValidationError

sku_bp = Blueprint("sku", __name__)


def _get_payload() -> dict:
    """Terima JSON maupun form-data (application/x-www-form-urlencoded)."""
    payload = request.get_json(silent=True)
    if payload is None:
        payload = request.form.to_dict()
    if not isinstance(payload, dict) or not payload:
        raise ValidationError("Body request kosong atau bukan JSON/form yang valid.")
    return payload


@sku_bp.get("/sku")
def get_skus():
    """Daftar Master SKU. Query opsional: ?q=<kata>&limit=<n>&offset=<n>."""
    limit = request.args.get("limit", type=int)
    if limit is not None:
        limit = max(limit, 1)
    offset = max(request.args.get("offset", 0, type=int), 0)
    return jsonify(sku_service.list_skus(request.args.get("q"), limit, offset)), 200


@sku_bp.post("/sku")
def create_sku():
    item = sku_service.create_sku(_get_payload())
    return jsonify({"status": "success", "message": "SKU berhasil ditambahkan.", "item": item}), 201


@sku_bp.put("/sku/<string:item_id>")
def update_sku(item_id: str):
    item = sku_service.update_sku(item_id, _get_payload())
    return jsonify({"status": "success", "message": "SKU berhasil diperbarui.", "item": item}), 200


@sku_bp.post("/sku/upload")
def upload_sku():
    file = request.files.get("file")
    if file is None or not file.filename:
        raise ValidationError("File tidak ditemukan. Kirim file Excel pada field 'file'.")
    return jsonify(sku_service.import_skus_from_file(file)), 200
