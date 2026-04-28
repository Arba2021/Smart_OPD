from fastapi import APIRouter, HTTPException, status, Header, Depends
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


async def verify_internal_key(x_api_key: str | None = Header(None)):
    if x_api_key is None:
        return None
    if x_api_key != "super_secret_internal_key_change_in_production":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
    return None


@router.post("/start")
async def start_disaster_simulation(payload: dict, _: dict = Depends(verify_internal_key)):
    try:
        scenario = payload.get("scenario", "dengue")
        patient_count = payload.get("patient_count", 100)
        
        # Return a mock successful response for the MVP demo
        return {
            "simulation_id": "sim-demo-001",
            "status": "CONTAINED",
            "message": f"Simulation for {scenario} with {patient_count} patients completed successfully.",
            "progress": 100,
            "current_phase": "CONTAINED",
            "metrics": {
                "patients_injected": patient_count,
                "cases_detected": 18,
                "confidence_percent": 94,
                "sms_alerts_sent": 50,
                "travel_prevented": 200,
                "early_warning_hours": 6
            }
        }
    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start simulation")


@router.get("/status/{sim_id}")
async def get_sim_status(sim_id: str, _: dict = Depends(verify_internal_key)):
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