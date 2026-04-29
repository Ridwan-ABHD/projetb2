from fastapi import APIRouter, HTTPException
from database import get_db_connection

router = APIRouter(prefix="/hives", tags=["ruches"])

@router.get("/")
def list_hives():
    """Liste TES ruches réelles à partir de la table ruches."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # On récupère les IDs réels (ceux que j'ai vus sur ta photo)
        cursor.execute("SELECT id_ruche FROM ruches")
        hives = cursor.fetchall()
        
        result = []
        for hive in hives:
            hid = hive['id_ruche']
            
            # On récupère la dernière mesure pour savoir si la ruche est "vivante"
            cursor.execute("""
                SELECT temperature, poids, frequence_moyenne, timestamp 
                FROM mesures 
                WHERE id_ruche = ? 
                ORDER BY timestamp DESC LIMIT 1
            """, (hid,))
            last = cursor.fetchone()
            
            result.append({
                "id": hid,
                "name": f"Ruche {hid}", # On génère un nom propre pour l'affichage
                "last_reading": dict(last) if last else None
            })
        return result

@router.get("/{hive_id}")
def get_hive(hive_id: str):
    """Détails d'une ruche spécifique."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # On vérifie si elle existe
        cursor.execute("SELECT id_ruche FROM ruches WHERE id_ruche = ?", (hive_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Ruche introuvable")
            
        # On récupère sa dernière mesure complète
        cursor.execute("""
            SELECT * FROM mesures 
            WHERE id_ruche = ? 
            ORDER BY timestamp DESC LIMIT 1
        """, (hive_id,))
        last = cursor.fetchone()
        
        return {
            "id": hive_id,
            "data": dict(last) if last else "Aucune donnée"
        }

@router.get("/{hive_id}/history")
def get_history(hive_id: str, limit: int = 50):
    """Historique des mesures pour les graphiques du dashboard."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, temperature, poids, frequence_moyenne 
            FROM mesures 
            WHERE id_ruche = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (hive_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
