from io import BytesIO
import pandas as pd
from sqlalchemy import func
from database import db
from models import MasterSKU, InboundHistory, InboundDetail
from services.exceptions import NotFoundError

def get_dashboard_stats():
    total_sku = db.session.query(func.count(MasterSKU.item_id)).scalar() or 0
    total_history = db.session.query(func.count(InboundHistory.history_id)).scalar() or 0
    
    last_upload = InboundHistory.query.filter_by(status="Success")\
        .order_by(InboundHistory.upload_time.desc()).first()

    return {
        "total_sku": total_sku,
        "total_history": total_history,
        "last_upload_file": last_upload.file_name if last_upload else "-",
        "last_upload_time": last_upload.upload_time.strftime("%d %b %Y, %H:%M") if last_upload else "-"
    }

def get_history_list():
    # Query gabungan hitung dinamis total_lines via COUNT(detail_id)
    results = db.session.query(
        InboundHistory,
        func.count(InboundDetail.detail_id).label("total_lines")
    ).outerjoin(InboundDetail, InboundHistory.history_id == InboundDetail.history_id)\
     .group_by(InboundHistory.history_id)\
     .order_by(InboundHistory.upload_time.desc()).all()

    output = []
    for history, lines in results:
        output.append({
            "history_id": history.history_id,
            "upload_time": history.upload_time.strftime("%d %b %Y, %H:%M"),
            "file_name": history.file_name,
            "containers": history.total_container,
            "lines": lines,
            "total_qty_cs": history.total_qty_cs,
            "required_pallets": history.total_required_pallets,
            "status": history.status
        })
    return output

def get_history_details(history_id):
    history = db.session.get(InboundHistory, history_id)
    if not history:
        raise NotFoundError("Data riwayat tidak ditemukan.")

    details = db.session.query(InboundDetail, MasterSKU.description, MasterSKU.cpp)\
        .join(MasterSKU, InboundDetail.item_id == MasterSKU.item_id)\
        .filter(InboundDetail.history_id == history_id).all()

    items = []
    for detail, desc, cpp in details:
        items.append({
            "container_number": detail.container_number,
            "batch_number": detail.batch_number,
            "item_id": detail.item_id,
            "description": desc,
            "cpp": cpp,
            "qty_carton": detail.qty_carton,
            "qty_pallet": detail.qty_pallet
        })
    return items

def generate_excel_report(history_id):
    history = db.session.get(InboundHistory, history_id)
    if not history:
        raise NotFoundError("Data riwayat tidak ditemukan.")

    items = get_history_details(history_id)
    df = pd.DataFrame(items)
    df.rename(columns={
        "container_number": "Container Number",
        "batch_number": "Batch Number",
        "item_id": "Item Number",
        "description": "Description",
        "cpp": "CPP",
        "qty_carton": "Qty CS",
        "qty_pallet": "Required Pallets"
    }, inplace=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inbound Result")
    output.seek(0)
    return output, f"Result_{history.file_name}"