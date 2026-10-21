"""Membaca & memvalidasi file Excel Master SKU menjadi list baris bersih."""
import logging

import pandas as pd

from services.exceptions import ValidationError
from services.sku_validation import validate_sku_fields

logger = logging.getLogger(__name__)

# nama kolom di Excel -> nama field internal
REQUIRED_COLUMNS = {"item number": "item_id", "description": "description", "cpp": "cpp"}
DISPLAY_COLUMNS = "Item Number, Description, CPP"


def _normalize_header(name) -> str:
    return " ".join(str(name).split()).casefold()


def parse_sku_file(file_storage) -> list[dict]:
    """Baca file .xlsx dan kembalikan list dict {item_id, description, cpp}.

    Semua-atau-tidak-sama-sekali: jika ada satu baris tidak valid, seluruh file
    ditolak (ValidationError) sehingga database tidak pernah terisi sebagian.
    """
    filename = (file_storage.filename or "").strip()
    if not filename.lower().endswith(".xlsx"):
        raise ValidationError("File harus berformat .xlsx.")

    try:
        # dtype=str menjaga item_id seperti '000123' tidak berubah jadi angka
        frame = pd.read_excel(file_storage.stream, sheet_name=0, dtype=str, engine="openpyxl")
    except Exception:  # file korup / bukan xlsx asli: apa pun penyebabnya, jawabannya 400
        logger.exception("Gagal membaca file Excel Master SKU")
        raise ValidationError("File tidak dapat dibaca. Pastikan file adalah Excel (.xlsx) yang valid.")

    headers = {_normalize_header(col): col for col in frame.columns}
    missing = [label for key, label in
               zip(REQUIRED_COLUMNS, ("Item Number", "Description", "CPP")) if key not in headers]
    if missing:
        found = ", ".join(str(c) for c in frame.columns) or "(kosong)"
        raise ValidationError(
            f"Struktur kolom tidak sesuai. Kolom wajib: {DISPLAY_COLUMNS}. "
            f"Kolom yang tidak ditemukan: {', '.join(missing)}. Kolom pada file: {found}."
        )

    frame = frame[[headers[key] for key in REQUIRED_COLUMNS]]
    frame.columns = list(REQUIRED_COLUMNS.values())
    frame = frame.dropna(how="all")
    if frame.empty:
        raise ValidationError("File tidak memiliki baris data.")

    # NaN -> None agar mudah dicek; index asli dipertahankan untuk nomor baris Excel
    frame = frame.astype(object).where(frame.notna(), None)

    rows: list[dict] = []
    errors: list[dict] = []
    first_seen: dict[str, int] = {}

    for index, record in zip(frame.index, frame.to_dict("records")):
        excel_row = int(index) + 2  # +1 header, +1 karena index mulai dari 0
        clean, row_errors = validate_sku_fields(
            record["item_id"], record["description"], record["cpp"], row=excel_row
        )
        if row_errors:
            errors.extend(row_errors)
            continue
        if clean["item_id"] in first_seen:
            errors.append({
                "row": excel_row,
                "field": "item_id",
                "message": f"Item Number duplikat dengan baris {first_seen[clean['item_id']]}.",
            })
            continue
        first_seen[clean["item_id"]] = excel_row
        rows.append(clean)

    if errors:
        raise ValidationError(
            f"Validasi file gagal ({len(errors)} kesalahan). Tidak ada data yang disimpan.", errors
        )
    return rows
