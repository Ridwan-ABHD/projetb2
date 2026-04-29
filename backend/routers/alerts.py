from fastapi import APIRouter, HTTPException
from database import get_db_connection

router = APIRouter(prefix="/alerts", tags=["alertes"])

@router.get("/")
def list_alerts():
    """Récupère les alertes en comparant mesures et règles"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Ta requête JOIN est excellente, on la garde !
        cursor.execute("""
            SELECT 
                m.id_mesure,
                m.id_ruche,
                m.timestamp,
                m.temperature,
                m.poids,
                m.frequence_moyenne,
                r.nom_alerte,
                r.description
            FROM mesures m
            JOIN regles_alerte r ON (
                m.temperature < r.temp_min
                OR m.frequence_moyenne > r.freq_max
                OR m.frequence_moyenne < r.freq_min
            )
            ORDER BY m.timestamp DESC
            LIMIT 50
        """)
        
        return [dict(row) for row in cursor.fetchall()]

@router.get("/config")
def get_thresholds():
    """Affiche les seuils de configuration de ta BDD"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM regles_alerte")
        return [dict(row) for row in cursor.fetchall()]

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    """Marque une alerte comme résolue dans la BDD"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # On vérifie d'abord si l'alerte existe (optionnel mais plus propre)
        cursor.execute("UPDATE alertes SET is_resolved = 1 WHERE id = ?", (alert_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Alerte introuvable")
            
        conn.commit()
        return {"status": "success", "message": f"Alerte {alert_id} résolue"}
