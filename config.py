"""Konfigurasi aplikasi. Semua nilai sensitif dibaca dari environment / .env."""
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _build_database_uri() -> str:
    explicit_uri = os.getenv("DATABASE_URL")
    if explicit_uri:
        return explicit_uri

    driver = os.getenv("DB_DRIVER", "mysql+pymysql")
    default_port = "5432" if driver.startswith("postgresql") else "3306"
    user = quote_plus(os.getenv("DB_USER", "root"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", default_port)
    name = os.getenv("DB_NAME", "db_whs_planner")

    credentials = f"{user}:{password}" if password else user
    uri = f"{driver}://{credentials}@{host}:{port}/{name}"
    if driver.startswith("mysql"):
        uri += "?charset=utf8mb4"
    return uri


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Connection pool: pre_ping membuang koneksi mati, recycle mencegah
    # "MySQL server has gone away" pada koneksi yang idle lama.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }

    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    ALLOWED_EXTENSIONS = {"xlsx"}
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200 MB

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

    def __init__(self):
        if self.SECRET_KEY == "dev-only-change-me":
            raise RuntimeError("SECRET_KEY wajib diatur pada environment production.")


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
