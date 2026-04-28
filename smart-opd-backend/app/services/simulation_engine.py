import logging
import random
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, func, text
from app.models.database import SessionLocal
from app.models.db_models import RegistrationQueue, DoctorQueue, PatientMaster, DoctorConfig, SimulationLog, SimulationStatus, HealthAlert
from app.services.ai_service import analyze_symptom_cluster

logger = logging.getLogger(__name__)

SCENARIOS = {
    "dengue": {
        "symptoms": [
            "High fever with severe body pain", "Fever and severe joint pain",
            "High fever with headache and body ache", "Severe body pain with high fever",
            "Fever with rash and body pain", "High fever with muscle pain",
            "Fever with severe headache and body pain", "Body pain with high fever and weakness"
        ],
        "expected_disease": "Dengue Fever"
    },
    "viral_fever": {
        "symptoms": [
            "Fever with sore throat", "Cough and body aches", "Fever and throat pain",
            "Sore throat with fever", "Fever with cough and cold", "Throat infection with fever",
            "Body ache with mild fever", "Fever with running nose"
        ],
        "expected_disease": "Viral Fever"
    },
    "cholera": {
        "symptoms": [
            "Severe diarrhea with dehydration", "Watery diarrhea and vomiting",
            "Diarrhea with muscle cramps", "Rapid dehydration and weakness",
            "Frequent watery stools and nausea", "Diarrhea with abdominal pain"
        ],
        "expected_disease": "Cholera"
    }
}

def _update_sim(db: Session, sim_id: str, **kwargs):
    sim = db.get(SimulationLog, sim_id)
    if sim:
        for k, v in kwargs.items():
            setattr(sim, k, v)
        db.commit()
        db.refresh(sim)

def run_simulation_pipeline(sim_id: str):
    db = SessionLocal()
    try:
        sim = db.get(SimulationLog, sim_id)
        if not sim:
            return
        
        scenario = sim.scenario
        count = sim.total_patients or 500
        scenario_data = SCENARIOS.get(scenario, SCENARIOS["dengue"])
        symptoms = scenario_data["symptoms"]
        
        # 🔥 CRITICAL FIX: Clear old simulation data before starting new run
        logger.info(f"Clearing old SIM-* data before starting simulation {sim_id}")
        db.execute(text("DELETE FROM doctor_queue WHERE doctor_token LIKE 'SIM-%'"))
        db.execute(text("DELETE FROM registration_queue WHERE reg_token LIKE 'SIM-%'"))
        db.execute(text("DELETE FROM patient_master WHERE phone LIKE '9999999%'"))
        db.commit()
        
        doctor = db.execute(select(DoctorConfig).where(DoctorConfig.doctor_id == "gen-001")).scalar_one_or_none()
        doctor_name = doctor.doctor_name if doctor else "Dr. Sharma"
        
        _update_sim(db, sim_id, status=SimulationStatus.INJECTING, progress=10)
        
        batch_size = 100
        sim_uuid = uuid.uuid4().hex[:6]
        
        for i in range(0, count, batch_size):
            end = min(i + batch_size, count)
            for j in range(i, end):
                phone = f"9999999{str(j).zfill(3)}"
                name = f"Patient_{scenario.upper()}_{j+1}"
                symptom = random.choice(symptoms)
                reg_token = f"SIM-{scenario.upper()}-{str(j+1).zfill(4)}-{sim_uuid}"
                doc_token = f"SIM-{scenario.upper()}-{str(j+1).zfill(4)}-{sim_uuid}"
                
                reg = RegistrationQueue(
                    name=name, phone=phone, reg_token=reg_token, 
                    status="REG_COMPLETED",
                    created_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 115))
                )
                db.add(reg)
                
                master = db.execute(select(PatientMaster).where(PatientMaster.phone == phone)).scalar_one_or_none()
                if not master:
                    db.add(PatientMaster(phone=phone, name=name))
                
                db.flush()
                
                doc_entry = DoctorQueue(
                    registration_id=reg.id,
                    doctor_id="gen-001",
                    doctor_name=doctor_name,
                    doctor_token=doc_token,
                    symptom=symptom,
                    triage_color="YELLOW" if scenario == "viral_fever" else "RED",
                    predicted_duration_mins=random.randint(8, 15),
                    ai_message=f"Token {doc_token} booked. Do not travel yet. Wait for SMS.",
                    status="WAITING",
                    created_at=reg.created_at
                )
                db.add(doc_entry)
            
            progress = 10 + int(((end) / count) * 40)
            _update_sim(db, sim_id, progress=min(progress, 50))
            db.commit()
        
        _update_sim(db, sim_id, total_patients=count, progress=50)
        _update_sim(db, sim_id, status=SimulationStatus.ANALYZING, progress=55)
        
        # Query ONLY current simulation's patients (using sim_uuid)
        patients = db.execute(
            select(DoctorQueue).where(DoctorQueue.doctor_token.like(f"SIM-{scenario.upper()}-%-{sim_uuid}"))
        ).scalars().all()
        
        symptom_list = [p.symptom for p in patients if p.symptom]
        _update_sim(db, sim_id, progress=65)
        
        logger.info(f"Analyzing {len(symptom_list)} symptoms for outbreak detection")
        ai_result = analyze_symptom_cluster(symptom_list)
        _update_sim(db, sim_id, progress=80)
        
        if ai_result.get("alert"):
            _update_sim(db, sim_id, 
                status=SimulationStatus.DETECTED,
                detected_disease=ai_result.get("suspected_disease", "Unknown"),
                confidence=int(ai_result.get("confidence", 0) * 100),
                matches=ai_result.get("match_count", 0),
                progress=90
            )
            logger.info(f"OUTBREAK DETECTED: {ai_result.get('suspected_disease')}")
        else:
            _update_sim(db, sim_id, status=SimulationStatus.CONTAINED, progress=100)
            return
        
        # CALCULATE REAL METRICS FROM DATABASE
        actual_injected = len(patients)
        actual_sms_sent = db.execute(
            select(func.count()).select_from(DoctorQueue).where(
                DoctorQueue.doctor_token.like(f"SIM-{scenario.upper()}-%-{sim_uuid}"),
                DoctorQueue.ai_message.isnot(None)
            )
        ).scalar() or 0
        
        actual_travel_prevented = db.execute(
            select(func.count(func.distinct(DoctorQueue.registration_id))).select_from(DoctorQueue).where(
                DoctorQueue.doctor_token.like(f"SIM-{scenario.upper()}-%-{sim_uuid}"),
                DoctorQueue.ai_message.isnot(None)
            )
        ).scalar() or 0
        
        first_patient_time = db.execute(
            select(func.min(DoctorQueue.created_at)).where(
                DoctorQueue.doctor_token.like(f"SIM-{scenario.upper()}-%-{sim_uuid}")
            )
        ).scalar()
        
        detection_time = datetime.now(timezone.utc)
        early_warning_hours = 0.0
        if first_patient_time:
            early_warning_hours = round((detection_time - first_patient_time).total_seconds() / 3600, 1)
        
        preventive_actions = {
            "sms_alerts_sent": actual_sms_sent,
            "travel_prevented": actual_travel_prevented,
            "beds_reserved": min(50, actual_injected // 10),
            "staff_notified": True,
            "public_health_alert": True
        }
        
        metrics = {
            "patients_injected": actual_injected,
            "cases_detected": ai_result.get("match_count", 0),
            "confidence_percent": int(ai_result.get("confidence", 0) * 100),
            "sms_alerts_sent": actual_sms_sent,
            "travel_prevented": actual_travel_prevented,
            "early_warning_hours": early_warning_hours,
            "detection_time_seconds": round((detection_time - first_patient_time).total_seconds(), 2) if first_patient_time else 0
        }
        
        logger.info(f"Simulation completed. Real metrics: {metrics}")
        
        _update_sim(db, sim_id, 
            status=SimulationStatus.CONTAINED,
            preventive_actions=preventive_actions,
            metrics=metrics,
            progress=100,
            completed_at=detection_time
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Simulation failed: {e}", exc_info=True)
        error_msg = str(e)[:490] + "..." if len(str(e)) > 500 else str(e)
        _update_sim(db, sim_id, status=SimulationStatus.FAILED, error_message=error_msg)
    finally:
        db.close()