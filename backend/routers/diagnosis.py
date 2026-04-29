import random
from fastapi import APIRouter, HTTPException
from database import get_db_connection
from pydantic import BaseModel

router = APIRouter(prefix="/diagnose", tags=["diagnostic IA"])

# On définit des modèles simples pour les échanges de données
class DiagnosisRequest(BaseModel):
    hive_id: str
    duration_seconds: int = 10

@router.post("/")
def run_diagnosis(req: DiagnosisRequest):
    """
    Simule une analyse IA en temps réel basée sur la 
    dernière fréquence enregistrée dans ta BDD.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. On vérifie si la ruche existe
        cursor.execute("SELECT id_ruche FROM ruches WHERE id_ruche = ?", (req.hive_id,))
        hive = cursor.fetchone()
        if not hive:
            raise HTTPException(status_code=404, detail="Ruche introuvable")

        # 2. On récupère la toute dernière fréquence (calculée par ton script analyse_ruche.py)
        cursor.execute("""
            SELECT frequence_moyenne FROM mesures 
            WHERE id_ruche = ? AND frequence_moyenne IS NOT NULL
            ORDER BY timestamp DESC LIMIT 1
        """, (req.hive_id,))
        last = cursor.fetchone()

    # 3. Logique de diagnostic basée sur TES vraies données
    # Si on n'a pas encore de mesure, on prend une base neutre
    freq = last['frequence_moyenne'] if last else 220.0

    if freq >= 280:
        prob = round(random.uniform(75, 95), 1)
        stress = "Élevé (Danger d'essaimage)"
        reco = "Diviser la colonie sous 48h : risque d'essaimage imminent."
    elif freq >= 260:
        prob = round(random.uniform(40, 74), 1)
        stress = "Modéré"
        reco = "Surveiller l'évolution. Inspecter la ruche d'ici 3 jours."
    else:
        prob = round(random.uniform(5, 39), 1)
        stress = "Normal"
        reco = "La colonie semble calme. Aucune intervention nécessaire."

    return {
        "hive_id": req.hive_id,
        "swarming_probability": prob,
        "dominant_frequency": freq,
        "stress_level": stress,
        "recommendation": reco,
        "analysis_duration": f"{req.duration_seconds}s"
    }
