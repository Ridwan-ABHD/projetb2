from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Alert
from schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alertes"])


@router.get("/", response_model=List[AlertOut])
def list_alerts(resolved: bool = False, db: Session = Depends(get_db)):
    return (
        db.query(Alert)
        .filter_by(is_resolved=resolved)
        .order_by(Alert.timestamp.desc())
        .all()
    )


@router.post("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    alert.is_resolved = True
    db.commit()
    db.refresh(alert)
    return alert
