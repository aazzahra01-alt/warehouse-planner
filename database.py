"""Inisialisasi SQLAlchemy (connection pool diatur lewat config)."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app) -> None:
    """Ikat instance `db` ke aplikasi Flask."""
    db.init_app(app)
