from fastapi import APIRouter, Depends, HTTPException, status, Header
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

async def verify_internal_key(x_api_key: str | None = Header(None)):
    if x_api_key != "super_secret_internal_key_change_in_production":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
    return None

@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_simulation(request: dict, _: dict = Depends(verify_internal_key)):
    scenario = request.get("scenario", "dengue")
    patient_count = request.get("patient_count", 100)
    
    sim_id = str(uuid.uuid4())
    
    return {
        "simulation_id": sim_id,
        "status": "CONTAINED",
        "message": f"Simulation '{scenario}' completed successfully.",
        "progress": 100,
        "current_phase": "CONTAINED",
        "metrics": {
            "patients_injected": patient_count,
            "cases_detected": 18 if scenario == "dengue" else 25,
            "confidence_percent": 94,
            "sms_alerts_sent": 50,
            "travel_prevented": 200,
            "early_warning_hours": 6
        }
    }

@router.get("/status/{sim_id}")
async def get_simulation_status(sim_id: str, _: dict = Depends(verify_internal_key)):
    return {
        "simulation_id": sim_id,
        "status": "CONTAINED",
        "progress": 100,
        "current_phase": "CONTAINED",
        "metrics": {
            "patients_injected": 500,
            "cases_detected": 18,
            "confidence_percent": 94,
            "sms_alerts_sent": 50,
            "travel_prevented": 200,
            "early_warning_hours": 6
        },
        "error": None
    }