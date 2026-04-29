from fastapi import APIRouter, HTTPException
from database import get_db_connection
from pydantic import BaseModel

router = APIRouter(prefix="/settings", tags=["paramètres"])

class SeuilUpdate(BaseModel):
    temp_min: float
    freq_min: float
    freq_max: float

@router.get("/")
def get_settings():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM regles_alerte")
        return [dict(row) for row in cursor.fetchall()]

@router.get("/{id_ruche}")
def get_hive_settings(id_ruche: str):
    """Récupère les seuils spécifiques à une ruche"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM regles_alerte WHERE id_ruche = ?", (id_ruche,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Réglages non trouvés pour cette ruche")
        return dict(row)

@router.put("/{id_ruche}")
def update_hive_settings(id_ruche: str, data: SeuilUpdate):
    """Met à jour les seuils de température d'une ruche"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE regles_alerte 
            SET temp_min = ?, freq_min = ?, freq_max = ? 
            WHERE id_ruche = ?
        """, (data.temp_min, data.freq_min, data.freq_max, id_ruche))
        
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ruche non trouvée dans les réglages")

    return data.model_dump()
