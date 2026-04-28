-- database/init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DO $$ BEGIN
    CREATE TYPE registration_status AS ENUM (
        'REG_WAITING',
        'REG_IN_PROGRESS',
        'REG_COMPLETED',
        'REG_ABANDONED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE doctor_queue_status AS ENUM (
        'WAITING',
        'CALLED',
        'IN_ROOM',
        'COMPLETED',
        'NO_SHOW',
        'SKIP',
        'EMERGENCY_PAUSED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE simulation_status AS ENUM (
        'PENDING',
        'INJECTING',
        'ANALYZING',
        'DETECTED',
        'CONTAINED',
        'FAILED'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS patient_master (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(15) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patient_master_phone ON patient_master(phone);

CREATE TABLE IF NOT EXISTS registration_queue (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    reg_token VARCHAR(50) UNIQUE NOT NULL,
    status registration_status DEFAULT 'REG_WAITING',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_registration_queue_phone ON registration_queue(phone);
CREATE INDEX IF NOT EXISTS idx_registration_queue_token ON registration_queue(reg_token);
CREATE INDEX IF NOT EXISTS idx_registration_queue_status ON registration_queue(status);

CREATE TABLE IF NOT EXISTS doctor_config (
    id SERIAL PRIMARY KEY,
    doctor_id VARCHAR(50) UNIQUE NOT NULL,
    doctor_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    max_daily_tokens INTEGER DEFAULT 80,
    buffer_time_seconds INTEGER DEFAULT 180,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_doctor_config_id ON doctor_config(doctor_id);

CREATE TABLE IF NOT EXISTS doctor_queue (
    id SERIAL PRIMARY KEY,
    registration_id INTEGER NOT NULL REFERENCES registration_queue(id) ON DELETE CASCADE,
    doctor_id VARCHAR(50) NOT NULL REFERENCES doctor_config(doctor_id) ON DELETE CASCADE,
    doctor_name VARCHAR(100) NOT NULL,
    doctor_token VARCHAR(50) NOT NULL,
    status doctor_queue_status DEFAULT 'WAITING',
    symptom TEXT,
    triage_color VARCHAR(10),
    predicted_duration_mins INTEGER DEFAULT 5,
    ai_message TEXT,
    called_at TIMESTAMPTZ,
    in_room_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_doctor_queue_token ON doctor_queue(doctor_token);
CREATE INDEX IF NOT EXISTS idx_doctor_queue_status ON doctor_queue(status);
CREATE INDEX IF NOT EXISTS idx_doctor_queue_doctor ON doctor_queue(doctor_id, status);
CREATE INDEX IF NOT EXISTS idx_doctor_queue_created ON doctor_queue(created_at);

CREATE TABLE IF NOT EXISTS health_alerts (
    id SERIAL PRIMARY KEY,
    suspected_disease VARCHAR(100) NOT NULL,
    confidence INTEGER NOT NULL CHECK (confidence >= 0 AND confidence <= 100),
    match_count INTEGER NOT NULL,
    trigger_symptoms TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'RESOLVED')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_health_alerts_status ON health_alerts(status);
CREATE INDEX IF NOT EXISTS idx_health_alerts_created ON health_alerts(created_at);

-- FIXED: simulation_logs table with TEXT for error_message and wider token fields
CREATE TABLE IF NOT EXISTS simulation_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario VARCHAR(50) NOT NULL,
    status simulation_status DEFAULT 'PENDING',
    progress INTEGER DEFAULT 0,
    total_patients INTEGER DEFAULT 0,
    detected_disease VARCHAR(100),
    confidence INTEGER,
    matches INTEGER,
    preventive_actions JSONB,
    metrics JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_simulation_logs_status ON simulation_logs(status);
CREATE INDEX IF NOT EXISTS idx_simulation_logs_started ON simulation_logs(started_at);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_patient_master_updated_at ON patient_master;
CREATE TRIGGER update_patient_master_updated_at
    BEFORE UPDATE ON patient_master
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_registration_queue_updated_at ON registration_queue;
CREATE TRIGGER update_registration_queue_updated_at
    BEFORE UPDATE ON registration_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_doctor_config_updated_at ON doctor_config;
CREATE TRIGGER update_doctor_config_updated_at
    BEFORE UPDATE ON doctor_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_doctor_queue_updated_at ON doctor_queue;
CREATE TRIGGER update_doctor_queue_updated_at
    BEFORE UPDATE ON doctor_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Seed doctor config
INSERT INTO doctor_config (doctor_id, doctor_name, department, max_daily_tokens, buffer_time_seconds)
VALUES
    ('gen-001', 'Dr. Sharma (General)', 'General', 80, 180),
    ('orth-002', 'Dr. Patel (Ortho)', 'Orthopedics', 80, 180),
    ('ped-003', 'Dr. Reddy (Pediatrics)', 'Pediatrics', 60, 240)
ON CONFLICT (doctor_id) DO UPDATE SET
    doctor_name = EXCLUDED.doctor_name,
    department = EXCLUDED.department,
    max_daily_tokens = EXCLUDED.max_daily_tokens,
    buffer_time_seconds = EXCLUDED.buffer_time_seconds,
    updated_at = NOW();

-- Views
CREATE OR REPLACE VIEW vw_active_doctor_queue AS
SELECT
    dq.id,
    dq.doctor_token,
    dq.doctor_name,
    dq.status,
    dq.triage_color,
    dq.symptom,
    dq.ai_message,
    dq.predicted_duration_mins,
    rq.name AS patient_name,
    rq.phone AS patient_phone,
    dq.created_at,
    dq.in_room_at,
    dq.called_at
FROM doctor_queue dq
JOIN registration_queue rq ON dq.registration_id = rq.id
WHERE dq.status IN ('WAITING', 'CALLED', 'IN_ROOM')
ORDER BY dq.created_at ASC;

CREATE OR REPLACE VIEW vw_today_bookings AS
SELECT
    doctor_id,
    COUNT(*) as total_bookings,
    COUNT(CASE WHEN status = 'WAITING' THEN 1 END) as waiting,
    COUNT(CASE WHEN status = 'CALLED' THEN 1 END) as called,
    COUNT(CASE WHEN status = 'IN_ROOM' THEN 1 END) as in_room,
    COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as completed
FROM doctor_queue
WHERE DATE(created_at) = CURRENT_DATE
GROUP BY doctor_id;

ANALYZE patient_master;
ANALYZE registration_queue;
ANALYZE doctor_config;
ANALYZE doctor_queue;
ANALYZE health_alerts;
ANALYZE simulation_logs;