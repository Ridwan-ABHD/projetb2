from fastapi import APIRouter, HTTPException
from database import get_db_connection

router = APIRouter(prefix="/hives", tags=["ruches"])


def _row_to_reading(row) -> dict | None:
    if not row:
        return None
    return {
        "id":           row["id_mesure"],
        "frequency_hz": row["frequence_moyenne"] or 0.0,
        "temperature_c": row["temperature"] or 0.0,
        "humidity_pct": row["humidite"] or 65.0,
        "weight_kg":    row["poids"] or 0.0,
        "timestamp":    row["timestamp"],
    }


@router.get("/")
def list_hives():
    with get_db_connection() as conn:
        hives = conn.execute("SELECT id_ruche, nom, localisation, statut FROM ruches").fetchall()
        result = []
        for h in hives:
            hid = h["id_ruche"]
            last = conn.execute("""
                SELECT id_mesure, timestamp, temperature, poids, frequence_moyenne, humidite
                FROM mesures WHERE id_ruche = ? ORDER BY timestamp DESC LIMIT 1
            """, (hid,)).fetchone()

            alerts = conn.execute("""
                SELECT id, id_ruche as hive_id, timestamp, type, message, severite as severity, is_resolved
                FROM alertes WHERE id_ruche = ? AND is_resolved = 0
            """, (hid,)).fetchall()

            result.append({
                "id":           hid,
                "name":         h["nom"] or f"Ruche {hid}",
                "location":     h["localisation"] or "",
                "status":       h["statut"] or "normal",
                "last_reading": _row_to_reading(last),
                "active_alerts": [dict(a) for a in alerts],
            })
        return result


@router.get("/{hive_id}")
def get_hive(hive_id: str):
    with get_db_connection() as conn:
        h = conn.execute(
            "SELECT id_ruche, nom, localisation, statut FROM ruches WHERE id_ruche = ?", (hive_id,)
        ).fetchone()
        if not h:
            raise HTTPException(status_code=404, detail="Ruche introuvable")

        last = conn.execute("""
            SELECT id_mesure, timestamp, temperature, poids, frequence_moyenne, humidite
            FROM mesures WHERE id_ruche = ? ORDER BY timestamp DESC LIMIT 1
        """, (hive_id,)).fetchone()

        alerts = conn.execute("""
            SELECT id, id_ruche as hive_id, timestamp, type, message, severite as severity, is_resolved
            FROM alertes WHERE id_ruche = ? AND is_resolved = 0
        """, (hive_id,)).fetchall()

        return {
            "id":           hive_id,
            "name":         h["nom"] or f"Ruche {hive_id}",
            "location":     h["localisation"] or "",
            "status":       h["statut"] or "normal",
            "last_reading": _row_to_reading(last),
            "active_alerts": [dict(a) for a in alerts],
        }


@router.get("/{hive_id}/history")
def get_history(hive_id: str, limit: int = 50):
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT id_mesure as id, timestamp, temperature as temperature_c,
                   poids as weight_kg, frequence_moyenne as frequency_hz, humidite as humidity_pct
            FROM mesures WHERE id_ruche = ? ORDER BY timestamp DESC LIMIT ?
        """, (hive_id, limit)).fetchall()
        return [dict(r) for r in rows]
