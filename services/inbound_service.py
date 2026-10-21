import math
from io import BytesIO
import pandas as pd
from sqlalchemy import func
from database import db
from models import MasterSKU, InboundHistory, InboundDetail
from services.exceptions import ValidationError, NotFoundError, ServiceError

REQUIRED_INBOUND_COLS = ["container number", "batch number", "item number", "qty cs"]


def _save_failed_history(filename):
    """Helper untuk menyimpan riwayat upload gagal ke database."""
    try:
        failed_history = InboundHistory(
            file_name=filename or "Failed_Upload.xlsx",
            total_container=0,
            total_qty_cs=0,
            total_required_pallets=0,
            status="Failed"
        )
        db.session.add(failed_history)
        db.session.commit()
    except Exception:
        db.session.rollback()


def process_inbound_file(file_storage):
    filename = (file_storage.filename or "").strip()

    try:
        if not filename.lower().endswith(".xlsx"):
            raise ValidationError("File harus berformat .xlsx.")

        try:
            file_bytes = BytesIO(file_storage.read())
            df = pd.read_excel(file_storage.stream, sheet_name=0, dtype=str, engine="openpyxl")
        except Exception:
            raise ValidationError("File Excel tidak dapat dibaca. Pastikan format file .xlsx valid.")

        # Normalisasi Header
        cols_map = {str(col).strip().lower(): col for col in df.columns}
        missing = [c for c in REQUIRED_INBOUND_COLS if c not in cols_map]
        if missing:
            raise ValidationError(f"Kolom wajib tidak ditemukan: {', '.join(missing)}")

        df = df[[cols_map[c] for c in REQUIRED_INBOUND_COLS]]
        df.columns = ["container_number", "batch_number", "item_id", "qty_carton"]
        df = df.dropna(how="all")

        if df.empty:
            raise ValidationError("File Excel tidak memiliki baris data.")

        # Clean Data & Convert Qty
        parsed_rows = []
        for idx, (_, row) in enumerate(df.iterrows()):
            excel_row = idx + 2
            item_id = str(row["item_id"]).strip() if pd.notna(row["item_id"]) else ""
            container = str(row["container_number"]).strip() if pd.notna(row["container_number"]) else ""
            batch = str(row["batch_number"]).strip() if pd.notna(row["batch_number"]) else ""
            
            try:
                qty = int(float(row["qty_carton"]))
                if qty <= 0:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValidationError(f"Baris {excel_row}: Qty CS harus berupa angka bulat positif.")

            if not item_id or not container or not batch:
                raise ValidationError(f"Baris {excel_row}: Container, Batch, dan Item Number wajib diisi.")

            parsed_rows.append({
                "container_number": container,
                "batch_number": batch,
                "item_id": item_id,
                "qty_carton": qty
            })

        # Konsolidasi Group By (Container + Batch + Item)
        grouped = {}
        for r in parsed_rows:
            key = (r["container_number"], r["batch_number"], r["item_id"])
            grouped[key] = grouped.get(key, 0) + r["qty_carton"]

        # Validasi Keberadaan Master SKU
        item_ids = list({k[2] for k in grouped.keys()})
        skus = MasterSKU.query.filter(MasterSKU.item_id.in_(item_ids)).all()
        sku_map = {s.item_id: s for s in skus}

        missing_skus = [iid for iid in item_ids if iid not in sku_map]
        if missing_skus:
            raise ValidationError(f"Proses dibatalkan. SKU berikut belum terdaftar di Master Data: {', '.join(missing_skus)}")

        # Hitung Pallet per Baris Group (ROUNDUP / math.ceil)
        detail_records = []
        total_qty_cs = 0
        total_required_pallets = 0
        unique_containers = set()
        unique_skus = set()

        for (container, batch, item_id), qty in grouped.items():
            cpp = sku_map[item_id].cpp
            qty_pallet = math.ceil(qty / cpp)

            total_qty_cs += qty
            total_required_pallets += qty_pallet
            unique_containers.add(container)
            unique_skus.add(item_id)

            detail_records.append({
                "container_number": container,
                "batch_number": batch,
                "item_id": item_id,
                "description": sku_map[item_id].description,
                "cpp": cpp,
                "qty_carton": qty,
                "qty_pallet": qty_pallet
            })

        # Transaksi Simpan Database
        history = InboundHistory(
            file_name=filename,
            total_container=len(unique_containers),
            total_qty_cs=total_qty_cs,
            total_required_pallets=total_required_pallets,
            status="Success"
        )
        db.session.add(history)
        db.session.flush()

        for d in detail_records:
            detail = InboundDetail(
                history_id=history.history_id,
                container_number=d["container_number"],
                batch_number=d["batch_number"],
                item_id=d["item_id"],
                qty_carton=d["qty_carton"],
                qty_pallet=d["qty_pallet"]
            )
            db.session.add(detail)

        db.session.commit()

        return {
            "status": "success",
            "history_id": history.history_id,
            "summary": {
                "total_sku": len(unique_skus),
                "total_qty_cs": total_qty_cs,
                "total_required_pallets": total_required_pallets,
                "total_containers": len(unique_containers)
            },
            "items": detail_records
        }

    except ValidationError as val_err:
        db.session.rollback()
        _save_failed_history(filename)
        raise val_err
    except Exception as exc:
        db.session.rollback()
        _save_failed_history(filename)
        raise ServiceError("Gagal menyimpan hasil perhitungan ke database.") from exc