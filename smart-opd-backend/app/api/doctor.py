from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from app.models.database import get_db
from app.models.schemas import DoctorActionRequest
from app.models.db_models import DoctorQueue, RegistrationQueue
from app.services.queue_engine import process_skip, process_emergency, calculate_moving_average_wait
from app.services.ai_service import generate_emergency_message, generate_status_sms, generate_complexity_warning, generate_walking_sms
from app.services.sms_service import send_sms_bulk, send_sms
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


async def verify_internal_key(x_api_key: str | None = Header(None)):
    if x_api_key is None:
        return None
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
    return None


@router.post("/call-next")
async def call_next_patient(request: Request, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        body = await request.json()
        doctor_id = body.get("doctor_id")
        
        next_patient = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                DoctorQueue.status == 'WAITING'
            ).order_by(DoctorQueue.created_at.asc()).with_for_update()
        ).scalars().first()
        
        if not next_patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No patients waiting in queue")
        
        next_patient.status = 'IN_ROOM'
        next_patient.in_room_at = datetime.now(timezone.utc)
        next_patient.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(next_patient)
        
        sms_text = generate_walking_sms(next_patient.doctor_name, next_patient.doctor_token)
        if next_patient.registration:
            await send_sms(next_patient.registration.phone, sms_text)
        
        return {
            "status": "SUCCESS",
            "message": "Patient called successfully",
            "patient": {
                "doctor_token": next_patient.doctor_token,
                "name": next_patient.registration.name if next_patient.registration else "Unknown",
                "triage_color": next_patient.triage_color
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Call next failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to call next patient")


@router.post("/done-next")
async def done_next(request: Request, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        body = await request.json()
        req = DoctorActionRequest(**body)
        
        current_in_room = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.doctor_id == req.doctor_id,
                DoctorQueue.status == 'IN_ROOM'
            )
        ).scalar_one_or_none()
        
        next_waiting = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.doctor_id == req.doctor_id,
                DoctorQueue.status == 'WAITING'
            ).order_by(DoctorQueue.created_at.asc()).with_for_update()
        ).scalars().first()
        
        if not next_waiting:
            if current_in_room:
                current_in_room.status = 'COMPLETED'
                current_in_room.updated_at = datetime.now(timezone.utc)
                db.commit()
                return {"status": "SUCCESS", "message": "Current patient completed, queue is now empty", "ai_message": None}
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No patients waiting in queue")
        
        if current_in_room:
            current_in_room.status = 'COMPLETED'
            next_waiting.status = 'IN_ROOM'
            next_waiting.in_room_at = datetime.now(timezone.utc)
            next_waiting.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            ai_warning = None
            if current_in_room.in_room_at:
                elapsed = (datetime.now(timezone.utc) - current_in_room.in_room_at).total_seconds() / 60
                avg = calculate_moving_average_wait(db, req.doctor_id) / 60
                if elapsed > avg * 2 and current_in_room.registration:
                    ai_warning = generate_complexity_warning(
                        current_in_room.registration.name,
                        int(elapsed),
                        int(avg)
                    )
            
            return {
                "status": "SUCCESS",
                "message": "Next patient moved to IN_ROOM",
                "ai_message": ai_warning
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Done-next failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process done-next")


@router.post("/skip")
async def skip_patient(request: Request, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        body = await request.json()
        req = DoctorActionRequest(**body)
        
        current = db.execute(select(DoctorQueue).where(DoctorQueue.id == req.doctor_queue_id)).scalar_one_or_none()
        if not current or current.status not in ['IN_ROOM', 'CALLED']:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient cannot be skipped in current state")
        
        process_skip(db, current, req.doctor_id)
        db.commit()
        
        return {"status": "SUCCESS", "message": "Patient skipped", "ai_message": None}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skip failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to skip patient")


@router.post("/emergency")
async def trigger_emergency(request: Request, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        body = await request.json()
        req = DoctorActionRequest(**body)
        
        waiting_patients = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.doctor_id == req.doctor_id,
                DoctorQueue.status.in_(['WAITING', 'CALLED'])
            )
        ).scalars().all()
        
        if not waiting_patients:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No patients in queue to pause")
        
        process_emergency(db, waiting_patients)
        db.commit()
        
        ai_message = generate_emergency_message()
        phones = [p.registration.phone for p in waiting_patients if p.registration]
        if phones:
            await send_sms_bulk(phones, ai_message)
        
        return {
            "status": "EMERGENCY_PAUSED",
            "affected_patients": len(waiting_patients),
            "ai_message": ai_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Emergency trigger failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to trigger emergency pause")


@router.get("/queue")
async def get_doctor_queue(doctor_id: str, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        active_record = db.execute(
            select(DoctorQueue).join(RegistrationQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                DoctorQueue.status == 'IN_ROOM'
            )
        ).scalar_one_or_none()
        
        upcoming_records = db.execute(
            select(DoctorQueue).join(RegistrationQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                DoctorQueue.status.in_(['WAITING', 'CALLED'])
            ).order_by(DoctorQueue.created_at.asc())
        ).scalars().all()
        
        remaining = db.execute(
            select(func.count()).select_from(DoctorQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                DoctorQueue.status.in_(['WAITING', 'CALLED', 'IN_ROOM'])
            )
        ).scalar()
        
        avg_time_seconds = calculate_moving_average_wait(db, doctor_id)
        avg_time_str = f"{int(avg_time_seconds // 60)} min" if avg_time_seconds > 0 else "0 min"
        
        eta_str = "--:--"
        if remaining and avg_time_seconds > 0:
            total_seconds = remaining * avg_time_seconds
            eta_time = datetime.now(timezone.utc) + timedelta(seconds=total_seconds)
            eta_str = eta_time.strftime("%I:%M %p")
        
        active_data = None
        ai_warning = None
        
        if active_record:
            if active_record.in_room_at and avg_time_seconds > 0:
                elapsed_seconds = (datetime.now(timezone.utc) - active_record.in_room_at).total_seconds()
                if elapsed_seconds > (avg_time_seconds * 2) and active_record.registration:
                    ai_warning = generate_complexity_warning(
                        active_record.registration.name,
                        int(elapsed_seconds // 60),
                        int(avg_time_seconds // 60)
                    )
            
            active_data = {
                "id": active_record.id,
                "doctor_token": active_record.doctor_token,
                "name": active_record.registration.name,
                "status": active_record.status,
                "triage_color": active_record.triage_color,
                "symptom": active_record.symptom
            }
        
        upcoming_data = [
            {
                "id": u.id,
                "doctor_token": u.doctor_token,
                "name": u.registration.name,
                "status": u.status,
                "triage_color": u.triage_color
            }
            for u in upcoming_records
        ]
        
        return {
            "active": active_data,
            "upcoming": upcoming_data,
            "metrics": {
                "avg_time": avg_time_str,
                "remaining": remaining or 0,
                "eta": eta_str
            },
            "ai_warning": ai_warning
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch doctor queue: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch doctor queue")