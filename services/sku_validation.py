"""Aturan validasi Master SKU, dipakai bersama oleh input manual & upload Excel."""
import re
from decimal import Decimal, InvalidOperation

ITEM_ID_MAX_LEN = 50
DESCRIPTION_MAX_LEN = 255
CPP_MAX = 2_147_483_647  # batas INT pada database

_FLOAT_LIKE_INT = re.compile(r"^\d+\.0+$")  # contoh: "1001.0" dari sel Excel numerik


def is_blank(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN
        return True
    return str(value).strip() == ""


def _normalize_item_id(value) -> str:
    text = str(value).strip()
    return text.split(".")[0] if _FLOAT_LIKE_INT.match(text) else text


def _parse_cpp(value) -> tuple[int | None, str | None]:
    """Return (nilai_int, pesan_error)."""
    try:
        number = Decimal(str(value).strip())
    except InvalidOperation:
        return None, "CPP harus berupa angka."
    if not number.is_finite():
        return None, "CPP harus berupa angka."
    if number != number.to_integral_value():
        return None, "CPP harus berupa bilangan bulat."
    if number <= 0:
        return None, "CPP harus lebih besar dari 0."
    if number > CPP_MAX:
        return None, "CPP terlalu besar."
    return int(number), None


def validate_sku_fields(item_id, description, cpp, row: int | None = None):
    """Validasi satu SKU.

    Return (data_bersih, daftar_error). `data_bersih` bernilai None jika ada error.
    `row` diisi nomor baris Excel agar pesan error mudah dilacak.
    """
    errors: list[dict] = []

    def add_error(field: str, message: str) -> None:
        entry = {"field": field, "message": message}
        if row is not None:
            entry = {"row": row, **entry}
        errors.append(entry)

    clean_item_id = clean_description = clean_cpp = None

    if is_blank(item_id):
        add_error("item_id", "Item Number tidak boleh kosong.")
    else:
        clean_item_id = _normalize_item_id(item_id)
        if len(clean_item_id) > ITEM_ID_MAX_LEN:
            add_error("item_id", f"Item Number maksimal {ITEM_ID_MAX_LEN} karakter.")

    if is_blank(description):
        add_error("description", "Description tidak boleh kosong.")
    else:
        clean_description = str(description).strip()
        if len(clean_description) > DESCRIPTION_MAX_LEN:
            add_error("description", f"Description maksimal {DESCRIPTION_MAX_LEN} karakter.")

    if is_blank(cpp):
        add_error("cpp", "CPP tidak boleh kosong.")
    else:
        clean_cpp, cpp_error = _parse_cpp(cpp)
        if cpp_error:
            add_error("cpp", cpp_error)

    if errors:
        return None, errors
    return {"item_id": clean_item_id, "description": clean_description, "cpp": clean_cpp}, []
