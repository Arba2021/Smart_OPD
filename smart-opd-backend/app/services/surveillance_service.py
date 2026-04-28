import logging
import re 
from sqlalchemy import select
from app.models.database import SessionLocal
from app.models.db_models import DoctorQueue, HealthAlert
from app.services.ai_service import analyze_symptom_cluster
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_surveillance_check():
    db = SessionLocal()
    try:
        two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
        results = db.execute(
            select(DoctorQueue.symptom).where(
                DoctorQueue.created_at >= two_hours_ago,
                DoctorQueue.symptom.isnot(None),
                DoctorQueue.symptom != ''
            )
        ).scalars().all()
        symptoms = [s for s in results if s.strip()]
        if len(symptoms) < 3:
            return

        logger.info(f"Surveillance analyzing {len(symptoms)} symptoms")
        ai_result = analyze_symptom_cluster(symptoms)

        if ai_result.get("alert"):
            existing_alert = db.execute(
                select(HealthAlert).where(
                    HealthAlert.suspected_disease == ai_result["suspected_disease"],
                    HealthAlert.status == 'ACTIVE'
                )
            ).scalar_one_or_none()
            if not existing_alert:
                new_alert = HealthAlert(
                    suspected_disease=ai_result["suspected_disease"],
                    match_count=ai_result["match_count"],
                    confidence=ai_result["confidence"],
                    trigger_symptoms=ai_result.get("trigger_symptoms", ""),
                    status='ACTIVE'
                )
                db.add(new_alert)
                db.commit()
                logger.info(f"HEALTH ALERT TRIGGERED: {ai_result['suspected_disease']}")
    except Exception as e:
        logger.error(f"Surveillance check failed: {e}")
        db.rollback()
    finally:
        db.close()