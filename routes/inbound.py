from flask import Blueprint, jsonify, request, send_file
from services import inbound_service, history_service
from services.exceptions import ValidationError

inbound_bp = Blueprint("inbound", __name__)

@inbound_bp.get("/dashboard")
def get_dashboard():
    return jsonify(history_service.get_dashboard_stats()), 200

@inbound_bp.post("/inbound/process")
def process_inbound():
    file = request.files.get("file")
    if not file or not file.filename:
        raise ValidationError("File tidak ditemukan. Kirim file Excel pada field 'file'.")
    return jsonify(inbound_service.process_inbound_file(file)), 200

@inbound_bp.get("/history")
def get_history():
    return jsonify(history_service.get_history_list()), 200

@inbound_bp.get("/history/<int:history_id>")
def get_history_detail(history_id):
    return jsonify(history_service.get_history_details(history_id)), 200

@inbound_bp.get("/history/<int:history_id>/export")
def export_history(history_id):
    excel_stream, download_name = history_service.generate_excel_report(history_id)
    return send_file(
        excel_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=download_name
    )