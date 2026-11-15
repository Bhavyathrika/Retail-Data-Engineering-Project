
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3307")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv(
        "DB_NAME",
        "data_engineering_project"
    )
}

if not DB_CONFIG["password"]:
    raise ValueError("DB_PASSWORD is missing from .env")
