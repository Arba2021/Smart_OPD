# smart-opd-backend/app/models/db_models.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum, Float, ForeignKey, Text, func
from sqlalchemy.orm import relationship, declarative_base
import enum
import uuid

Base = declarative_base()

class RegistrationStatus(str, enum.Enum):
    REG_WAITING = "REG_WAITING"
    REG_IN_PROGRESS = "REG_IN_PROGRESS"
    REG_COMPLETED = "REG_COMPLETED"
    REG_ABANDONED = "REG_ABANDONED"

class DoctorQueueStatus(str, enum.Enum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    IN_ROOM = "IN_ROOM"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    SKIP = "SKIP"
    EMERGENCY_PAUSED = "EMERGENCY_PAUSED"

class SimulationStatus(str, enum.Enum):
    PENDING = "PENDING"
    INJECTING = "INJECTING"
    ANALYZING = "ANALYZING"
    DETECTED = "DETECTED"
    CONTAINED = "CONTAINED"
    FAILED = "FAILED"

class PatientMaster(Base):
    __tablename__ = "patient_master"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # REMOVED: doctor_queues relationship - causes join ambiguity

class RegistrationQueue(Base):
    __tablename__ = "registration_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(15), nullable=False, index=True)
    reg_token = Column(String(20), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(RegistrationStatus), default=RegistrationStatus.REG_WAITING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DoctorConfig(Base):
    __tablename__ = "doctor_config"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(String(50), unique=True, nullable=False, index=True)
    doctor_name = Column(String(100), nullable=False)
    department = Column(String(100))
    max_daily_tokens = Column(Integer, default=80)
    buffer_time_seconds = Column(Integer, default=180)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class DoctorQueue(Base):
    __tablename__ = "doctor_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    registration_id = Column(Integer, ForeignKey("registration_queue.id", ondelete="CASCADE"), nullable=False)
    doctor_id = Column(String(50), nullable=False, index=True)
    doctor_name = Column(String(100), nullable=False)
    doctor_token = Column(String(20), nullable=False, index=True)
    status = Column(SQLEnum(DoctorQueueStatus), default=DoctorQueueStatus.WAITING)
    symptom = Column(Text, nullable=True)
    triage_color = Column(String(10), nullable=True)
    predicted_duration_mins = Column(Integer, default=5)
    ai_message = Column(Text, nullable=True)
    called_at = Column(DateTime(timezone=True), nullable=True)
    in_room_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    registration = relationship("RegistrationQueue", back_populates="doctor_entries")

# Add reverse relationship on RegistrationQueue
RegistrationQueue.doctor_entries = relationship(
    "DoctorQueue",
    back_populates="registration",
    cascade="all, delete-orphan"
)

class HealthAlert(Base):
    __tablename__ = "health_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    suspected_disease = Column(String(100), nullable=False)
    confidence = Column(Integer, nullable=False)
    match_count = Column(Integer, nullable=False)
    trigger_symptoms = Column(Text, nullable=False)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class SimulationLog(Base):
    __tablename__ = "simulation_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scenario = Column(String(50), nullable=False)
    status = Column(SQLEnum(SimulationStatus), default=SimulationStatus.PENDING)
    progress = Column(Integer, default=0)
    total_patients = Column(Integer, default=0)
    detected_disease = Column(String(100), nullable=True)
    confidence = Column(Integer, nullable=True)
    matches = Column(Integer, nullable=True)
    preventive_actions = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String(500), nullable=True)