import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from datetime import date
from app.core.config import settings
from app.models.database import get_db
from app.models.db_models import RegistrationQueue, PatientMaster, DoctorQueue, DoctorConfig
from app.models.schemas import AddPatientRequest, AssignDoctorRequest
from app.services.sms_service import send_sms

router = APIRouter()
logging.basicConfig(level=logging.INFO)


async def verify_internal_key(x_api_key: str | None = Header(None)):
    if x_api_key is None:
        return None
    if x_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
    return None


@router.get("/queue")
async def get_registration_queue(db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        query = select(RegistrationQueue).where(
            RegistrationQueue.status.in_(['REG_WAITING', 'REG_IN_PROGRESS'])
        ).order_by(RegistrationQueue.created_at.asc(), RegistrationQueue.id.asc())
        patients = db.execute(query).scalars().all()
        return [
            {"id": p.id, "name": p.name, "phone": p.phone, "reg_token": p.reg_token, "status": p.status}
            for p in patients
        ]
    except Exception as e:
        logging.error(f"Fetch queue failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch queue")


@router.post("/add", status_code=status.HTTP_201_CREATED)
async def add_patient(request: Request, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        body = await request.json()
        req = AddPatientRequest(**body)
        today = date.today()
        
        existing = db.execute(
            select(RegistrationQueue).where(
                RegistrationQueue.phone == req.phone,
                func.date(RegistrationQueue.created_at) == today,
                RegistrationQueue.status.in_(['REG_WAITING', 'REG_IN_PROGRESS'])
            )
        ).scalar_one_or_none()
        
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient already in active registration queue today")

        master = db.execute(select(PatientMaster).where(PatientMaster.phone == req.phone)).scalar_one_or_none()
        final_name = master.name if master else req.name.strip().title()

        if not master:
            db.add(PatientMaster(phone=req.phone, name=final_name))
        
        count = db.execute(
            select(func.count()).select_from(RegistrationQueue).where(func.date(RegistrationQueue.created_at) == today)
        ).scalar()
        reg_token = f"REG-{str(count + 1).zfill(4)}"
        new_patient = RegistrationQueue(name=final_name, phone=req.phone, reg_token=reg_token)
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)

        try:
            await send_sms(req.phone, f"Your registration token is {reg_token}. Wait for your name to be called at the counter.")
        except Exception:
            logging.error(f"Failed to send SMS to {req.phone}")

        return {"id": new_patient.id, "reg_token": new_patient.reg_token, "status": new_patient.status, "name": final_name}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Add patient failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add patient")


@router.post("/call-next")
async def call_next(db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    logging.info("HIT CALL NEXT ENDPOINT")
    try:
        query = select(RegistrationQueue).where(
            RegistrationQueue.status == 'REG_WAITING'
        ).order_by(
            RegistrationQueue.created_at.asc(),
            RegistrationQueue.id.asc()
        ).with_for_update()
        
        patient = db.execute(query).scalars().first()
        if not patient:
            logging.warning("No patients waiting in registration queue")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No patients waiting in registration queue")

        logging.info(f"Moving patient {patient.reg_token} to IN_PROGRESS")
        patient.status = 'REG_IN_PROGRESS'
        db.commit()
        return {"id": patient.id, "name": patient.name, "phone": patient.phone, "reg_token": patient.reg_token}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Call next DB error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")


@router.post("/assign-doctor")
async def assign_doctor(request: Request, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        body = await request.json()
        req = AssignDoctorRequest(**body)
        
        reg = db.execute(select(RegistrationQueue).where(RegistrationQueue.id == req.registration_id)).scalar_one_or_none()
        if not reg or reg.status != 'REG_IN_PROGRESS':
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient is not currently in progress")

        doc_config = db.execute(select(DoctorConfig).where(DoctorConfig.doctor_id == req.doctor_id)).scalar_one_or_none()
        if not doc_config:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor configuration not found")

        existing_doc = db.execute(
            select(DoctorQueue).join(RegistrationQueue).where(
                RegistrationQueue.phone == reg.phone,
                DoctorQueue.doctor_id == req.doctor_id,
                func.date(DoctorQueue.created_at) == date.today(),
                DoctorQueue.status.in_(['WAITING', 'CALLED', 'IN_ROOM'])
            )
        ).scalar_one_or_none()
        
        if existing_doc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient already has an active token for this doctor today")

        count = db.execute(
            select(func.count()).select_from(DoctorQueue).where(DoctorQueue.doctor_id == req.doctor_id, func.date(DoctorQueue.created_at) == date.today())
        ).scalar()
        
        if count >= doc_config.max_daily_tokens:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Daily token limit reached for this doctor")

        doc_token = f"DOC-{req.doctor_id[:3].upper()}-{str(count + 1).zfill(3)}"
        doc_entry = DoctorQueue(registration_id=reg.id, doctor_id=req.doctor_id, doctor_name=doc_config.doctor_name, doctor_token=doc_token)
        reg.status = 'REG_COMPLETED'
        db.add(doc_entry)
        db.commit()
        return {"doctor_token": doc_token, "status": "WAITING"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Assign doctor failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign doctor")


@router.post("/restore-late")
async def restore_late(request: Request, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    try:
        body = await request.json()
        reg_id = body.get("registration_id")
        if not reg_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing registration_id")
        
        doc_entry = db.execute(select(DoctorQueue).where(DoctorQueue.registration_id == reg_id)).scalar_one_or_none()
        if not doc_entry or doc_entry.status not in ['NO_SHOW', 'SKIP']:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No valid record found to restore")

        doc_entry.status = 'WAITING'
        doc_entry.called_at = None
        doc_entry.in_room_at = None
        db.commit()
        return {"detail": "Patient restored to end of queue", "doctor_token": doc_entry.doctor_token}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Restore late failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to restore patient")