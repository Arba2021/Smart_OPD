# app/api/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.models.database import get_db
from app.models.db_models import HealthAlert, DoctorQueue
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

router = APIRouter()

class DismissRequest(BaseModel):
    pass

@router.get("/alerts")
async def get_active_alerts(db: Session = Depends(get_db)):
    alerts = db.execute(
        select(HealthAlert).where(
            HealthAlert.status == 'ACTIVE'
        ).order_by(desc(HealthAlert.created_at)).limit(10)
    ).scalars().all()
    
    return [
        {
            "id": a.id,
            "suspected_disease": a.suspected_disease,
            "match_count": a.match_count,
            "confidence": a.confidence,
            "trigger_symptoms": a.trigger_symptoms,
            "created_at": a.created_at.isoformat()
        }
        for a in alerts
    ]

@router.post("/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.execute(
        select(HealthAlert).where(HealthAlert.id == alert_id)
    ).scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        
    alert.status = 'DISMISSED'
    db.commit()
    
    return {"status": "DISMISSED"}

@router.get("/recent-symptoms")
async def get_recent_symptoms(db: Session = Depends(get_db)):
    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    results = db.execute(
        select(DoctorQueue.symptom, DoctorQueue.created_at).where(
            DoctorQueue.created_at >= two_hours_ago,
            DoctorQueue.symptom.isnot(None),
            DoctorQueue.symptom != ''
        ).order_by(desc(DoctorQueue.created_at)).limit(30)
    ).all()
    
    return [
        {
            "symptom": r.symptom,
            "time": r.created_at.strftime("%I:%M %p")
        }
        for r in results
    ]