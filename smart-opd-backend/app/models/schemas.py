from pydantic import BaseModel
from typing import Optional

class WebBookingRequest(BaseModel):
    name: str
    phone: str
    doctor_id: str
    symptom: Optional[str] = None

class StatusResponse(BaseModel):
    doctor_token: str
    status: str
    wait_minutes: int
    patients_ahead: int
    triage_color: str
    ai_message: Optional[str] = None

class DoctorActionRequest(BaseModel):
    doctor_id: str
    doctor_queue_id: int

class AddPatientRequest(BaseModel):
    name: str
    phone: str

class AssignDoctorRequest(BaseModel):
    registration_id: int
    doctor_id: str

class SimulationStartRequest(BaseModel):
    scenario: str
    patient_count: int = 500

class DisasterMetrics(BaseModel):
    patients_injected: int
    cases_detected: int
    confidence_percent: int
    sms_alerts_sent: int
    travel_prevented: int
    early_warning_hours: float

class SimulationStatusResponse(BaseModel):
    simulation_id: str
    status: str
    progress: int
    current_phase: str
    metrics: Optional[DisasterMetrics] = None
    error: Optional[str] = None