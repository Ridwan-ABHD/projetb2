from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Hive, SensorReading, Alert
from schemas import HiveOut, SensorReadingOut

router = APIRouter(prefix="/hives", tags=["ruches"])


@router.get("/", response_model=List[HiveOut])
def list_hives(db: Session = Depends(get_db)):
    hives = db.query(Hive).all()
    result = []
    for hive in hives:
        last = (
            db.query(SensorReading)
            .filter_by(hive_id=hive.id)
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        active_alerts = db.query(Alert).filter_by(hive_id=hive.id, is_resolved=False).all()
        result.append(
            HiveOut(
                id=hive.id,
                name=hive.name,
                location=hive.location,
                status=hive.status,
                last_reading=last,
                active_alerts=active_alerts,
            )
        )
    return result


@router.get("/{hive_id}", response_model=HiveOut)
def get_hive(hive_id: int, db: Session = Depends(get_db)):
    hive = db.get(Hive, hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Ruche introuvable")
    last = (
        db.query(SensorReading)
        .filter_by(hive_id=hive.id)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )
    active_alerts = db.query(Alert).filter_by(hive_id=hive.id, is_resolved=False).all()
    return HiveOut(
        id=hive.id,
        name=hive.name,
        location=hive.location,
        status=hive.status,
        last_reading=last,
        active_alerts=active_alerts,
    )


@router.get("/{hive_id}/history", response_model=List[SensorReadingOut])
def get_history(hive_id: int, limit: int = 50, db: Session = Depends(get_db)):
    if not db.get(Hive, hive_id):
        raise HTTPException(status_code=404, detail="Ruche introuvable")
    return (
        db.query(SensorReading)
        .filter_by(hive_id=hive_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )
