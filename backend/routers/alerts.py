from fastapi import APIRouter, HTTPException
from database import get_db_connection

router = APIRouter(prefix="/alerts", tags=["alertes"])


@router.get("/")
def list_alerts(resolved: bool = False):
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT id, id_ruche as hive_id, timestamp, type, message, severite as severity, is_resolved
            FROM alertes WHERE is_resolved = ?
            ORDER BY timestamp DESC LIMIT 100
        """, (1 if resolved else 0,)).fetchall()
        return [dict(r) for r in rows]


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    with get_db_connection() as conn:
        conn.execute("UPDATE alertes SET is_resolved = 1 WHERE id = ?", (alert_id,))
        if conn.execute("SELECT changes()").fetchone()[0] == 0:
            raise HTTPException(status_code=404, detail="Alerte introuvable")
        conn.commit()
    return {"status": "success"}
