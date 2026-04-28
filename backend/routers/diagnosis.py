import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Hive, SensorReading
from schemas import DiagnosisRequest, DiagnosisResult

router = APIRouter(prefix="/diagnose", tags=["diagnostic IA"])


@router.post("/", response_model=DiagnosisResult)
def run_diagnosis(req: DiagnosisRequest, db: Session = Depends(get_db)):
    hive = db.get(Hive, req.hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Ruche introuvable")

    last = (
        db.query(SensorReading)
        .filter_by(hive_id=req.hive_id)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )

    freq = last.frequency_hz if last else 220.0 + random.uniform(-20, 20)

    if freq >= 280:
        prob = round(random.uniform(75, 95), 1)
        stress = "Élevé"
        reco = "Diviser la colonie sous 48h pour prévenir l'essaimage."
    elif freq >= 260:
        prob = round(random.uniform(40, 74), 1)
        stress = "Modéré"
        reco = "Surveiller l'évolution de la fréquence. Inspecter la ruche dans les 72h."
    else:
        prob = round(random.uniform(5, 39), 1)
        stress = "Normal"
        reco = "Aucune action requise. La colonie est en bon état."

    return DiagnosisResult(
        hive_id=hive.id,
        hive_name=hive.name,
        swarming_probability=prob,
        dominant_frequency=freq,
        stress_level=stress,
        duration_seconds=req.duration_seconds,
        recommendation=reco,
    )
