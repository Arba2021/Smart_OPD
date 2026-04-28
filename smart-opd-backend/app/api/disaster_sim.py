# smart-opd-backend/app/api/disaster_sim.py
from fastapi import APIRouter, Depends, HTTPException, status, Header, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select  # ✅ ADDED: Missing import
from app.models.database import get_db
from app.models.schemas import SimulationStartRequest, SimulationStatusResponse, DisasterMetrics
from app.services.simulation_engine import run_simulation_pipeline
from app.models.db_models import SimulationLog
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def verify_internal_key(x_api_key: str | None = Header(None)):
    if x_api_key is None:
        return None
    if x_api_key != "super_secret_internal_key_change_in_production":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")
    return None

@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_simulation(request: SimulationStartRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    if request.scenario not in ["dengue", "viral_fever", "cholera"]:
        raise HTTPException(status_code=400, detail="Invalid scenario. Use: dengue, viral_fever, cholera")

    # Prevent overlapping simulations
    active_sim = db.execute(
        select(SimulationLog).where(SimulationLog.status.in_(["PENDING", "INJECTING", "ANALYZING"]))
    ).scalar_one_or_none()
    if active_sim:
        raise HTTPException(status_code=409, detail="A simulation is already running. Wait for completion or check /status.")

    sim = SimulationLog(scenario=request.scenario, total_patients=request.patient_count)
    db.add(sim)
    db.commit()
    db.refresh(sim)

    background_tasks.add_task(run_simulation_pipeline, sim.id)
    return {"simulation_id": sim.id, "status": "STARTED", "message": f"Simulation '{request.scenario}' started. Poll /status/{sim.id} for progress."}

@router.get("/status/{sim_id}", response_model=SimulationStatusResponse)
async def get_simulation_status(sim_id: str, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    sim = db.get(SimulationLog, sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    # Force refresh from database
    db.refresh(sim)
    
    logger.info(f"Status check for {sim_id}: status={sim.status}, progress={sim.progress}, has_metrics={sim.metrics is not None}")
    
    metrics = DisasterMetrics(**sim.metrics) if sim.metrics else None
    return SimulationStatusResponse(
        simulation_id=sim.id,
        status=sim.status,
        progress=sim.progress,
        current_phase=sim.status,
        metrics=metrics,
        error=sim.error_message
    )

@router.post("/force-analyze/{sim_id}")
async def force_analysis(sim_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), _: dict = Depends(verify_internal_key)):
    sim = db.get(SimulationLog, sim_id)
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not found")
    if sim.status not in ["INJECTING", "PENDING"]:
        raise HTTPException(status_code=400, detail="Simulation must be in PENDING or INJECTING state")
    background_tasks.add_task(run_simulation_pipeline, sim_id)
    return {"status": "ANALYSIS_TRIGGERED", "message": "AI analysis queued."}