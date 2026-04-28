from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.models.db_models import DoctorQueue
from app.core.config import settings
from app.services.ai_service import predict_consultation_duration
import logging

logger = logging.getLogger(__name__)


def get_patient_wait_time(db: Session, doctor_id: str, current_patient_id: int) -> int:
    try:
        ahead_count = db.execute(
            select(func.count()).select_from(DoctorQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                DoctorQueue.status.in_(['IN_ROOM', 'CALLED']),
                DoctorQueue.id < current_patient_id
            )
        ).scalar() or 0
        
        avg_time = calculate_moving_average_wait(db, doctor_id)
        if avg_time == 0:
            avg_time = 300
        
        buffer_overhead = (ahead_count + 1) * settings.BUFFER_TIME_SECONDS
        return int((ahead_count * avg_time) + buffer_overhead)
        
    except Exception as e:
        logger.error(f"Error calculating wait time: {e}")
        return 0


def calculate_moving_average_wait(db: Session, doctor_id: str, window: int = 5) -> int:
    try:
        completed = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                DoctorQueue.status == 'COMPLETED',
                DoctorQueue.in_room_at.isnot(None)
            ).order_by(DoctorQueue.updated_at.desc()).limit(window)
        ).scalars().all()
        
        if not completed:
            return 0
        
        durations = []
        for c in completed:
            if c.in_room_at and c.updated_at:
                diff = (c.updated_at - c.in_room_at).total_seconds()
                if 60 < diff < 3600:
                    durations.append(diff)
        
        return int(sum(durations) / len(durations)) if durations else 0
        
    except Exception as e:
        logger.error(f"Error calculating moving average: {e}")
        return 0


def process_done_next(db: Session, current: DoctorQueue, doctor_id: str):
    try:
        current.status = 'COMPLETED'
        current.updated_at = datetime.now(timezone.utc)
        
        next_waiting = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                DoctorQueue.status == 'WAITING'
            ).order_by(DoctorQueue.created_at.asc()).with_for_update()
        ).scalars().first()
        
        if next_waiting:
            next_waiting.status = 'IN_ROOM'
            next_waiting.in_room_at = datetime.now(timezone.utc)
            next_waiting.updated_at = datetime.now(timezone.utc)
            
    except Exception as e:
        logger.error(f"Done next failed: {e}")
        db.rollback()
        raise


def process_skip(db: Session, current: DoctorQueue, doctor_id: str):
    try:
        current.status = 'SKIP'
        current.updated_at = datetime.now(timezone.utc)
        
        next_waiting = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.doctor_id == doctor_id,
                DoctorQueue.status == 'WAITING'
            ).order_by(DoctorQueue.created_at.asc()).with_for_update()
        ).scalars().first()
        
        if next_waiting:
            next_waiting.status = 'IN_ROOM'
            next_waiting.in_room_at = datetime.now(timezone.utc)
            next_waiting.updated_at = datetime.now(timezone.utc)
            
    except Exception as e:
        logger.error(f"Skip failed: {e}")
        db.rollback()
        raise


def process_emergency(db: Session, waiting_patients: list):
    try:
        for p in waiting_patients:
            p.status = 'EMERGENCY_PAUSED'
            p.updated_at = datetime.now(timezone.utc)
            
    except Exception as e:
        logger.error(f"Emergency pause failed: {e}")
        db.rollback()
        raise


async def check_buffer_and_noshow():
    from app.models.database import SessionLocal
    from app.services.sms_service import send_sms
    from app.services.ai_service import generate_walking_sms
    
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        buffer_threshold = now - timedelta(seconds=settings.BUFFER_TIME_SECONDS)
        noshow_threshold = now - timedelta(seconds=settings.NOSHOW_TIME_SECONDS)
        
        in_room_patients = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.status == 'IN_ROOM',
                DoctorQueue.in_room_at.isnot(None),
                DoctorQueue.in_room_at < buffer_threshold
            )
        ).scalars().all()
        
        for patient in in_room_patients:
            next_waiting = db.execute(
                select(DoctorQueue).where(
                    DoctorQueue.doctor_id == patient.doctor_id,
                    DoctorQueue.status == 'WAITING'
                ).order_by(DoctorQueue.created_at.asc()).with_for_update()
            ).scalars().first()
            
            if next_waiting:
                next_waiting.status = 'CALLED'
                next_waiting.called_at = now
                next_waiting.updated_at = now
                
                message = generate_walking_sms(next_waiting.doctor_name, next_waiting.doctor_token)
                if next_waiting.registration:
                    await send_sms(next_waiting.registration.phone, message)
        
        if in_room_patients:
            db.commit()
        
        no_shows = db.execute(
            select(DoctorQueue).where(
                DoctorQueue.status == 'CALLED',
                DoctorQueue.called_at.isnot(None),
                DoctorQueue.called_at < noshow_threshold
            )
        ).scalars().all()
        
        if no_shows:
            for patient in no_shows:
                patient.status = 'NO_SHOW'
                patient.updated_at = now
            db.commit()
            
    except Exception as e:
        logger.error(f"Buffer/Noshow check failed: {e}")
        db.rollback()
    finally:
        db.close()