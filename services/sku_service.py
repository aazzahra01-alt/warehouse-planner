"""Logika bisnis Master SKU: baca, tambah, ubah, dan UPSERT massal."""
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database import db
from models import MasterSKU
from services.exceptions import ConflictError, NotFoundError, ServiceError, ValidationError
from services.sku_excel import parse_sku_file
from services.sku_validation import validate_sku_fields

UPSERT_CHUNK_SIZE = 500


# --------------------------------------------------------------------- READ
def list_skus(search: str | None = None, limit: int | None = None, offset: int = 0) -> dict:
    query = MasterSKU.query
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            MasterSKU.item_id.ilike(pattern) | MasterSKU.description.ilike(pattern)
        )

    total = query.count()
    query = query.order_by(MasterSKU.item_id).offset(offset)
    if limit:
        query = query.limit(limit)
    rows = query.all()
    return {"total": total, "count": len(rows), "items": [row.to_dict() for row in rows]}


# ------------------------------------------------------------------- CREATE
def create_sku(payload: dict) -> dict:
    clean, errors = validate_sku_fields(
        payload.get("item_id"), payload.get("description"), payload.get("cpp")
    )
    if errors:
        raise ValidationError("Data SKU tidak valid.", errors)

    if db.session.get(MasterSKU, clean["item_id"]):
        raise ConflictError(f"Item Number '{clean['item_id']}' sudah terdaftar.")

    sku = MasterSKU(**clean)
    db.session.add(sku)
    try:
        db.session.commit()
    except IntegrityError:  # dua request bersamaan dengan item_id sama
        db.session.rollback()
        raise ConflictError(f"Item Number '{clean['item_id']}' sudah terdaftar.")
    return sku.to_dict()


# ------------------------------------------------------------------- UPDATE
def update_sku(item_id: str, payload: dict) -> dict:
    sku = db.session.get(MasterSKU, item_id)
    if sku is None:
        raise NotFoundError(f"Item Number '{item_id}' tidak ditemukan.")

    body_item_id = payload.get("item_id")
    if body_item_id not in (None, "") and str(body_item_id).strip() != item_id:
        raise ValidationError("Item Number tidak dapat diubah. Hapus lalu buat SKU baru.")

    clean, errors = validate_sku_fields(item_id, payload.get("description"), payload.get("cpp"))
    if errors:
        raise ValidationError("Data SKU tidak valid.", errors)

    sku.description = clean["description"]
    sku.cpp = clean["cpp"]
    db.session.commit()
    return sku.to_dict()


# ------------------------------------------------------------ UPLOAD (UPSERT)
def import_skus_from_file(file_storage) -> dict:
    rows = parse_sku_file(file_storage)  # raise ValidationError jika file/baris tidak valid

    try:
        updated = 0
        for start in range(0, len(rows), UPSERT_CHUNK_SIZE):
            chunk = rows[start:start + UPSERT_CHUNK_SIZE]
            ids = [row["item_id"] for row in chunk]
            updated += db.session.query(func.count(MasterSKU.item_id)) \
                .filter(MasterSKU.item_id.in_(ids)).scalar()
            db.session.execute(_build_upsert(chunk))
        db.session.commit()  # satu transaksi: semua tersimpan atau tidak sama sekali
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise ServiceError("Gagal menyimpan data ke database.") from exc

    return {
        "status": "success",
        "message": "Master SKU berhasil diperbarui.",
        "total_rows": len(rows),
        "inserted": len(rows) - updated,
        "updated": updated,
    }


def _build_upsert(rows: list[dict]):
    """INSERT ... ON DUPLICATE KEY UPDATE (MySQL) / ON CONFLICT DO UPDATE (PostgreSQL)."""
    dialect = db.engine.dialect.name

    if dialect in ("mysql", "mariadb"):
        from sqlalchemy.dialects.mysql import insert
        stmt = insert(MasterSKU).values(rows)
        # updated_at diurus otomatis oleh ON UPDATE CURRENT_TIMESTAMP di kolom
        return stmt.on_duplicate_key_update(
            description=stmt.inserted.description, cpp=stmt.inserted.cpp
        )

    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
        stmt = insert(MasterSKU).values(rows)
        return stmt.on_conflict_do_update(
            index_elements=[MasterSKU.item_id],
            set_={
                "description": stmt.excluded.description,
                "cpp": stmt.excluded.cpp,
                "updated_at": func.now(),  # PostgreSQL tidak punya ON UPDATE otomatis
            },
        )

    if dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
        stmt = insert(MasterSKU).values(rows)
        return stmt.on_conflict_do_update(
            index_elements=[MasterSKU.item_id],
            set_={
                "description": stmt.excluded.description,
                "cpp": stmt.excluded.cpp
            }
        )

    raise ServiceError(f"Database '{dialect}' belum didukung untuk UPSERT.")
