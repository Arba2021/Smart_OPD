from fastapi import APIRouter, HTTPException, Request, status, Depends
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.database import get_db
from app.models.db_models import RegistrationQueue, DoctorQueue, DoctorConfig, PatientMaster
from app.models.schemas import WebBookingRequest, StatusResponse
from app.services.ai_service import generate_booking_sms, generate_cutoff_sms, triage_symptom, parse_delay_from_reply, predict_consultation_duration
from app.services.sms_service import send_sms
from app.services.queue_engine import get_patient_wait_time
import logging
import re
import json

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/public-queue-count")
async def get_public_queue_count(doctor_id: str, db: Session = Depends(get_db)):
    try:
        count = db.execute(
            select(func.count()).select_from(DoctorQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                func.date(DoctorQueue.created_at) == date.today(),
                DoctorQueue.status.in_(['WAITING', 'CALLED', 'IN_ROOM'])
            )
        ).scalar()
        return {"count": count or 0}
    except Exception:
        return {"count": 0}


@router.get("/patient/lookup")
async def lookup_patient(phone: str, db: Session = Depends(get_db)):
    patient = db.execute(select(PatientMaster).where(PatientMaster.phone == phone)).scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    visits = db.execute(
        select(func.count()).select_from(DoctorQueue).join(RegistrationQueue).where(RegistrationQueue.phone == phone)
    ).scalar()
    return {"name": patient.name, "phone": patient.phone, "visits": visits}


@router.post("/book", status_code=status.HTTP_201_CREATED)
async def public_booking(request: Request, db: Session = Depends(get_db)):
    try:
        # Safely parse JSON
        try:
            body = await request.json()
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON in request body"
            )
        
        req = WebBookingRequest(**body)
        language = body.get("language", "en")
        
        doc_config = db.execute(select(DoctorConfig).where(DoctorConfig.doctor_id == req.doctor_id)).scalar_one_or_none()
        if not doc_config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Doctor selected")

        existing = db.execute(
            select(DoctorQueue).join(RegistrationQueue).where(
                RegistrationQueue.phone == req.phone,
                DoctorQueue.doctor_id == req.doctor_id,
                func.date(DoctorQueue.created_at) == date.today(),
                DoctorQueue.status.in_(['WAITING', 'CALLED', 'IN_ROOM'])
            )
        ).scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have an active token for this doctor today")

        # Generate unique token with collision handling
        while True:
            current_count = db.execute(
                select(func.count()).select_from(DoctorQueue).where(
                    DoctorQueue.doctor_id == req.doctor_id,
                    func.date(DoctorQueue.created_at) == date.today(),
                    DoctorQueue.status.in_(['WAITING', 'CALLED', 'IN_ROOM', 'COMPLETED', 'NO_SHOW', 'SKIP'])
                )
            ).scalar()
            
            reg_token = f"WEB-{str(current_count + 1).zfill(4)}"
            
            existing_token = db.execute(
                select(RegistrationQueue).where(RegistrationQueue.reg_token == reg_token)
            ).scalar_one_or_none()
            
            if not existing_token:
                break
            
            current_count += 1

        if current_count >= doc_config.max_daily_tokens:
            cutoff_msg = generate_cutoff_sms(req.name, doc_config.doctor_name, language)
            try:
                await send_sms(req.phone, cutoff_msg)
            except Exception as e:
                logger.error(f"Failed to send cutoff SMS: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "CUTOFF",
                    "message": "Token limit reached",
                    "ai_message": cutoff_msg,
                    "patient": req.name
                }
            )

        # AI triage with fallback
        ai_triage = {"color": "GREEN", "reason": "Routine", "complexity": 1}
        if req.symptom:
            try:
                ai_triage = triage_symptom(req.symptom, doc_config.doctor_name, language)
            except Exception as e:
                logger.warning(f"Triage AI failed, using fallback: {e}")
        
        triage_color = ai_triage.get("color", "GREEN")
        
        # Predict duration with fallback
        predicted_mins = 5
        if req.symptom:
            try:
                predicted_mins = predict_consultation_duration(req.symptom)
            except Exception as e:
                logger.warning(f"Duration prediction failed, using default: {e}")

        # Create registration
        reg = RegistrationQueue(name=req.name.strip().title(), phone=req.phone, reg_token=reg_token, status='REG_COMPLETED')
        db.add(reg)
        
        # Update or create patient master
        master = db.execute(select(PatientMaster).where(PatientMaster.phone == req.phone)).scalar_one_or_none()
        if not master:
            db.add(PatientMaster(phone=req.phone, name=req.name.strip().title()))
        db.flush()

        # Create doctor queue entry
        doc_token = f"DOC-{req.doctor_id[:3].upper()}-{str(current_count + 1).zfill(3)}"
        
        # Generate AI SMS
        ai_message = generate_booking_sms(req.name, doc_token, doc_config.doctor_name, language)
        
        doc_entry = DoctorQueue(
            registration_id=reg.id,
            doctor_id=req.doctor_id,
            doctor_name=doc_config.doctor_name,
            doctor_token=doc_token,
            symptom=req.symptom,
            triage_color=triage_color,
            predicted_duration_mins=predicted_mins,
            ai_message=ai_message  # Save AI message to database
        )
        db.add(doc_entry)
        db.commit()
        db.refresh(doc_entry)

        # Send SMS
        try:
            await send_sms(req.phone, ai_message)
        except Exception as e:
            logger.error(f"Failed to send booking SMS: {e}")

        return {
            "doctor_token": doc_token,
            "status": "WAITING",
            "message": "Do not come to the hospital until you receive a 'Start Walking' SMS.",
            "ai_message": ai_message,
            "triage": ai_triage
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Booking failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Booking failed")


@router.post("/webhook/missed-call", response_model=StatusResponse)
async def missed_call_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        phone = payload.get("phone") or payload.get("Number")
        if not phone:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing phone")
        
        clean_phone = re.sub(r'\D', '', phone)[-10:]
        if not re.match(r'^[6-9]\d{9}$', clean_phone):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone")

        doc = db.execute(
            select(DoctorQueue).join(RegistrationQueue).where(
                RegistrationQueue.phone == clean_phone,
                DoctorQueue.status.in_(['WAITING', 'CALLED', 'IN_ROOM'])
            ).order_by(DoctorQueue.created_at.desc())
        ).scalar_one_or_none()

        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NO_ACTIVE_TOKEN")

        wait_time = get_patient_wait_time(db, doc.doctor_id, doc.id)
        ahead_count = db.execute(
            select(func.count()).select_from(DoctorQueue).where(
                DoctorQueue.doctor_id == doc.doctor_id,
                DoctorQueue.status.in_(['IN_ROOM', 'CALLED', 'WAITING']),
                DoctorQueue.id < doc.id
            )
        ).scalar()

        return StatusResponse(
            doctor_token=doc.doctor_token,
            status=doc.status,
            wait_minutes=wait_time // 60,
            patients_ahead=ahead_count,
            triage_color=doc.triage_color,
            ai_message=doc.ai_message  # Return AI message
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="WEBHOOK_ERROR")


@router.post("/webhook/sms-reply")
async def sms_reply_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        message = payload.get("message", "")
        phone = payload.get("phone", "")
        
        clean_phone = re.sub(r'\D', '', str(phone))[-10:]
        if not clean_phone or not re.match(r'^[6-9]\d{9}$', clean_phone):
            return {"status": "ERROR", "detail": "Invalid phone"}
        
        if not message:
            return {"status": "ERROR", "detail": "Empty message"}

        ai_parsed = {"intent": "UNKNOWN", "delay_minutes": 0}
        try:
            ai_parsed = parse_delay_from_reply(message)
        except Exception as e:
            logger.warning(f"SMS reply parsing failed: {e}")
        
        intent = ai_parsed.get("intent", "UNKNOWN")
        delay_minutes = ai_parsed.get("delay_minutes", 0)

        if intent == "CANCEL":
            doc = db.execute(
                select(DoctorQueue).join(RegistrationQueue).where(
                    RegistrationQueue.phone == clean_phone,
                    DoctorQueue.status.in_(['WAITING', 'CALLED'])
                ).order_by(DoctorQueue.created_at.desc())
            ).scalars().first()
            if doc:
                doc.status = 'SKIP'
                db.commit()
                return {"status": "CANCELLED", "token": doc.doctor_token}
        elif intent == "LATE" and delay_minutes > 0:
            doc = db.execute(
                select(DoctorQueue).join(RegistrationQueue).where(
                    RegistrationQueue.phone == clean_phone,
                    DoctorQueue.status == 'CALLED'
                ).order_by(DoctorQueue.created_at.desc())
            ).scalars().first()
            if doc and doc.called_at:
                future_time = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
                doc.called_at = future_time
                db.commit()
                return {"status": "DELAY_UPDATED", "delay_minutes": delay_minutes, "token": doc.doctor_token}

        return {"status": "RECEIVED", "intent": intent, "delay_minutes": delay_minutes}
    except Exception as e:
        return {"status": "ERROR", "detail": str(e)}


@router.get("/patient/track")
async def track_patient(phone: str, doctor_id: str, db: Session = Depends(get_db)):
    doc = db.execute(
        select(DoctorQueue).join(RegistrationQueue).where(
            RegistrationQueue.phone == phone,
            DoctorQueue.doctor_id == doctor_id,
            DoctorQueue.status.in_(['WAITING', 'CALLED', 'IN_ROOM'])
        ).order_by(DoctorQueue.created_at.desc())
    ).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NO_ACTIVE_TOKEN")

    ahead_records = db.execute(
        select(DoctorQueue).where(
            DoctorQueue.doctor_id == doctor_id,
            DoctorQueue.status.in_(['IN_ROOM', 'CALLED', 'WAITING']),
            DoctorQueue.created_at < doc.created_at
        ).order_by(DoctorQueue.created_at.asc())
    ).scalars().all()

    total_mins_ahead = sum(r.predicted_duration_mins for r in ahead_records)
    now = datetime.now(timezone.utc)
    eta_time = now + timedelta(minutes=total_mins_ahead)
    formatted_eta = eta_time.strftime("%I:%M %p")

    return {
        "doctor_token": doc.doctor_token,
        "status": doc.status,
        "patients_ahead": len(ahead_records),
        "expected_wait_mins": total_mins_ahead,
        "suggested_arrival_time": formatted_eta,
        "ai_message": doc.ai_message  # Return AI message
    }