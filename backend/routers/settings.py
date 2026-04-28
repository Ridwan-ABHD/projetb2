from typing import Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Threshold
from schemas import ThresholdUpdate

router = APIRouter(prefix="/settings", tags=["paramètres"])

_DEFAULTS: Dict[str, float] = {
    "freq_warning": 260.0,
    "freq_critical": 280.0,
    "temp_warning": 36.0,
    "temp_critical": 38.0,
    "humidity_min": 50.0,
    "humidity_max": 80.0,
    "weight_drop_threshold": 2.0,
}


@router.get("/", response_model=Dict[str, float])
def get_settings(db: Session = Depends(get_db)):
    result = dict(_DEFAULTS)
    for row in db.query(Threshold).all():
        result[row.key] = row.value
    return result


@router.put("/", response_model=Dict[str, float])
def update_settings(data: ThresholdUpdate, db: Session = Depends(get_db)):
    for key, value in data.model_dump().items():
        row = db.get(Threshold, key)
        if row:
            row.value = value
        else:
            db.add(Threshold(key=key, value=value))
    db.commit()
    return data.model_dump()
