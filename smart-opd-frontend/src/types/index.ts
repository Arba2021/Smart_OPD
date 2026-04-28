export type Language = 'en' | 'hi' | 'te' | 'ta' | 'bn' | 'mr'

export interface RegistrationPatient {
  id: number
  name: string
  phone: string
  reg_token: string
  status: 'REG_WAITING' | 'REG_IN_PROGRESS' | 'REG_COMPLETED' | 'REG_ABANDONED'
  created_at: string
}

export interface DoctorQueuePatient {
  id: number
  registration_id: number
  doctor_id: string
  doctor_name: string
  doctor_token: string
  status: 'WAITING' | 'CALLED' | 'IN_ROOM' | 'COMPLETED' | 'NO_SHOW' | 'SKIP' | 'EMERGENCY_PAUSED'
  name?: string
  phone?: string
  triage_color?: 'RED' | 'YELLOW' | 'GREEN'
  symptom?: string
  predicted_duration_mins?: number
  ai_message?: string  // NEW
}

export interface DoctorMetrics {
  avg_time: string
  remaining: number
  eta: string
}

export interface BookingResponse {
  doctor_token: string
  status: string
  message: string
  ai_message: string
  ai_message_full?: string
  triage?: {
    color: string
    reason: string
    complexity: number
  }
}

export interface StatusResponse {
  doctor_token: string
  status: string
  wait_minutes: number
  patients_ahead: number
  triage_color: string
  ai_message?: string  // NEW
}

export interface PatientMaster {
  name: string
  phone: string
  visits: number
}

export interface SmsLog {
  text: string
  time: string
  type?: 'info' | 'error' | 'success'
}