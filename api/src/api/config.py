import os
from pathlib import Path

LOCAL_DATABASE_URL = "postgresql+psycopg://rol_api:rol_api@127.0.0.1:5432/observatorio"


def database_url() -> str:
    return os.getenv("API_DATABASE_URL", LOCAL_DATABASE_URL)


def ranking_manifest() -> Path:
    default = Path(__file__).resolve().parents[3] / "etl/datos/crudo/MANIFEST.csv"
    return Path(os.getenv("API_RANKING_MANIFEST", str(default)))
