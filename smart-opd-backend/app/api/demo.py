from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
from datetime import datetime, timezone, date
from app.models.database import get_db
from app.models.db_models import DoctorQueue, RegistrationQueue, PatientMaster, DoctorConfig
from app.services.surveillance_service import run_surveillance_check
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


async def verify_internal_key(x_api_key: str | None = Header(None)):
    if x_api_key is None:
        return None
    if x_api_key != "super_secret_internal_key_change_in_production":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
    return None


@router.post("/seed-all")
async def seed_demo_data(db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        # Clear existing demo data
        db.execute(text("DELETE FROM doctor_queue WHERE doctor_token LIKE 'DEMO%'"))
        db.execute(text("DELETE FROM registration_queue WHERE reg_token LIKE 'DEMO%'"))
        db.execute(text("DELETE FROM patient_master WHERE phone LIKE '9999999%'"))
        db.execute(text("DELETE FROM health_alerts"))
        db.commit()

        categories = {"dengue": 18, "viral": 18, "normal": 15}
        symptoms = {
            "dengue": [
                "High fever with severe body pain", "Fever and severe joint pain",
                "High fever with headache and body ache", "Severe body pain with high fever",
                "Fever with rash and body pain", "High fever with muscle pain",
                "Fever with severe headache and body pain", "Body pain with high fever and weakness",
                "High fever with joint pain and rash", "Severe fever with body ache",
                "Fever with bone pain and headache", "High fever with severe muscle pain",
                "Fever with body pain and weakness", "High fever with joint and muscle pain",
                "Severe body pain with fever", "Fever with severe headache",
                "High fever with rash and joint pain", "Body pain with fever and weakness"
            ],
            "viral": [
                "Fever with sore throat", "Cough and body aches", "Fever and throat pain",
                "Sore throat with fever", "Fever with cough and cold", "Throat infection with fever",
                "Body ache with mild fever", "Fever with running nose", "Cough with fever and weakness",
                "Sore throat and body pain", "Fever with throat irritation", "Mild fever with cough",
                "Fever with cold and cough", "Throat pain with fever", "Body pain with sore throat",
                "Fever with headache and cough", "Cough with throat pain", "Fever with body weakness"
            ],
            "normal": [
                "Regular checkup", "Knee pain", "Eye infection", "Stomach pain",
                "Back pain", "Dental checkup", "Skin rash", "Ear pain",
                "Headache", "Routine blood test", "Vaccination", "Health checkup",
                "Allergy", "Chest pain", "Thyroid checkup"
            ]
        }

        triage_map = {"dengue": "RED", "viral": "YELLOW", "normal": "GREEN"}
        duration_map = {"dengue": 12, "viral": 8, "normal": 5}
        tokens_created = []
        count = 0

        for cat, num in categories.items():
            for i in range(num):
                phone = f"9999999{str(100 + count).zfill(2)}"
                name = f"Patient_{count + 1}"
                symptom = symptoms[cat][i]
                
                reg_token = f"DEMO-{cat.upper()}-{str(count + 1).zfill(3)}"
                doc_token = f"DEMO-{cat.upper()}-{str(count + 1).zfill(3)}"
                
                reg = RegistrationQueue(name=name, phone=phone, reg_token=reg_token, status='REG_COMPLETED')
                db.add(reg)
                
                master = db.execute(select(PatientMaster).where(PatientMaster.phone == phone)).scalar_one_or_none()
                if not master:
                    db.add(PatientMaster(phone=phone, name=name))
                db.flush()
                
                doc_entry = DoctorQueue(
                    registration_id=reg.id,
                    doctor_id="gen-001",
                    doctor_name="Dr. Sharma (General)",
                    doctor_token=doc_token,
                    symptom=symptom,
                    triage_color=triage_map[cat],
                    predicted_duration_mins=duration_map[cat],
                    ai_message=f"Token {doc_token} booked for Dr. Sharma. Do not travel yet. Wait for SMS.",
                    status="WAITING",
                    created_at=datetime.now(timezone.utc)
                )
                db.add(doc_entry)
                tokens_created.append(doc_token)
                count += 1
        
        db.commit()
        logger.info(f"Demo data seeded: {len(tokens_created)} patients")
        return {
            "status": "SUCCESS",
            "message": f"Seeded {len(tokens_created)} demo patients across 3 categories",
            "categories": categories,
            "sample_tokens": tokens_created[:5]
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Demo seed failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to seed demo data")


@router.post("/analyze-now")
async def trigger_analysis(db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        await run_surveillance_check()
        return {"status": "SUCCESS", "message": "AI surveillance analysis completed. Check Radar page."}
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to run analysis")


@router.get("/status")
async def demo_status(db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    total = db.execute(select(func.count()).select_from(DoctorQueue)).scalar()
    alerts = db.execute(select(func.count()).select_from(health_alerts).where(health_alerts.status == 'ACTIVE')).scalar()
    return {"total_patients": total, "active_alerts": alerts, "ready": total > 0}