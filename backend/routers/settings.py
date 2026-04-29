from fastapi import APIRouter
from database import get_db_connection
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["paramètres"])


class AppSettings(BaseModel):
    freq_warning:          float
    freq_critical:         float
    temp_warning:          float
    temp_critical:         float
    humidity_min:          float
    humidity_max:          float
    weight_drop_threshold: float


def _ensure_row(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id                    INTEGER PRIMARY KEY CHECK (id = 1),
            freq_warning          REAL DEFAULT 260,
            freq_critical         REAL DEFAULT 280,
            temp_warning          REAL DEFAULT 36,
            temp_critical         REAL DEFAULT 38,
            humidity_min          REAL DEFAULT 50,
            humidity_max          REAL DEFAULT 80,
            weight_drop_threshold REAL DEFAULT 2
        )
    """)
    conn.execute("""
        INSERT OR IGNORE INTO settings (id, freq_warning, freq_critical, temp_warning,
            temp_critical, humidity_min, humidity_max, weight_drop_threshold)
        VALUES (1, 260, 280, 36, 38, 50, 80, 2)
    """)
    conn.commit()


@router.get("/", response_model=AppSettings)
def get_settings():
    with get_db_connection() as conn:
        _ensure_row(conn)
        row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
        return dict(row)


@router.put("/", response_model=AppSettings)
def save_settings(data: AppSettings):
    with get_db_connection() as conn:
        _ensure_row(conn)
        conn.execute("""
            UPDATE settings SET
                freq_warning          = ?,
                freq_critical         = ?,
                temp_warning          = ?,
                temp_critical         = ?,
                humidity_min          = ?,
                humidity_max          = ?,
                weight_drop_threshold = ?
            WHERE id = 1
        """, (
            data.freq_warning, data.freq_critical, data.temp_warning,
            data.temp_critical, data.humidity_min, data.humidity_max,
            data.weight_drop_threshold,
        ))
        conn.commit()
    return data
