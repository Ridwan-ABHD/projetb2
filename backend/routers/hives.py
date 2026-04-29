from fastapi import APIRouter, HTTPException
from database import get_db_connection

router = APIRouter(prefix="/hives", tags=["ruches"])


# --- DANS TON FICHIER hives.py ---

def _row_to_reading(row) -> dict | None:
    if not row:
        return None
    
    # Correction : on vérifie la présence des clés de manière plus sûre
    # et on s'assure que frequency_hz reçoit bien la valeur de frequence_moyenne
    return {
        "id":            row["id_mesure"],
        "frequency_hz":  row["frequence_moyenne"] if row["frequence_moyenne"] is not None else 0.0,
        "temperature_c": row["temperature"] if row["temperature"] is not None else 0.0,
        "humidity_pct":  65.0, # Valeur fixe si tu n'as pas de capteur d'humidité
        "weight_kg":     row["poids"] if row["poids"] is not None else 0.0,
        "timestamp":     row["timestamp"],
    }

@router.get("/")
def list_hives():
    with get_db_connection() as conn:
        hives = conn.execute("SELECT id_ruche, id_site, type_ruche FROM ruches").fetchall()
        result = []
        for h in hives:
            hid = h["id_ruche"]
            # IMPORTANT : On s'assure de bien prendre frequence_moyenne ici
            last = conn.execute("""
                SELECT id_mesure, timestamp, temperature, poids, frequence_moyenne
                FROM mesures 
                WHERE id_ruche = ? 
                AND frequence_moyenne IS NOT NULL 
                ORDER BY timestamp DESC LIMIT 1
            """, (hid,)).fetchone()
            
            # Si aucune ligne avec fréquence n'existe, on prend la toute dernière mesure quand même
            if not last:
                last = conn.execute("""
                    SELECT id_mesure, timestamp, temperature, poids, frequence_moyenne
                    FROM mesures WHERE id_ruche = ? ORDER BY timestamp DESC LIMIT 1
                """, (hid,)).fetchone()

            alerts = conn.execute("""
                SELECT id, id_ruche as hive_id, timestamp, type, message, severite as severity, is_resolved
                FROM alertes WHERE id_ruche = ? AND is_resolved = 0
            """, (hid,)).fetchall()

            severities = [a["severity"] for a in alerts]
            status = "critical" if "critical" in severities else \
                     "warning"  if "warning"  in severities else "normal"

            result.append({
                "id":           hid,
                "name":         hid,
                "location":     h["id_site"] or "",
                "status":       status,
                "last_reading": _row_to_reading(last),
                "active_alerts": [dict(a) for a in alerts],
            })
        return result


@router.get("/{hive_id}")
def get_hive(hive_id: str):
    with get_db_connection() as conn:
        h = conn.execute(
            "SELECT id_ruche, id_site, type_ruche FROM ruches WHERE id_ruche = ?", (hive_id,)
        ).fetchone()
        if not h:
            raise HTTPException(status_code=404, detail="Ruche introuvable")

        last = conn.execute("""
            SELECT id_mesure, timestamp, temperature, poids, frequence_moyenne
            FROM mesures WHERE id_ruche = ? ORDER BY timestamp DESC LIMIT 1
        """, (hive_id,)).fetchone()

        alerts = conn.execute("""
            SELECT id, id_ruche as hive_id, timestamp, type, message, severite as severity, is_resolved
            FROM alertes WHERE id_ruche = ? AND is_resolved = 0
        """, (hive_id,)).fetchall()

        severities = [a["severity"] for a in alerts]
        status = "critical" if "critical" in severities else \
                 "warning"  if "warning"  in severities else "normal"

        return {
            "id":           hive_id,
            "name":         hive_id,
            "location":     h["id_site"] or "",
            "status":       status,
            "last_reading": _row_to_reading(last),
            "active_alerts": [dict(a) for a in alerts],
        }


@router.get("/{hive_id}/history")
def get_history(hive_id: str, limit: int = 50):
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT id_mesure as id, timestamp, temperature as temperature_c,
                   poids as weight_kg, frequence_moyenne as frequency_hz
            FROM mesures WHERE id_ruche = ? ORDER BY timestamp DESC LIMIT ?
        """, (hive_id, limit)).fetchall()
        return [{**dict(r), "humidity_pct": 65.0} for r in rows]
