"""Logika pengecekan kesehatan aplikasi & koneksi database."""
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import db


def check_database() -> tuple[bool, str | None]:
    """Jalankan `SELECT 1`. Return (berhasil, pesan_error)."""
    try:
        db.session.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError as exc:
        db.session.rollback()
        return False, str(exc.__cause__ or exc)
