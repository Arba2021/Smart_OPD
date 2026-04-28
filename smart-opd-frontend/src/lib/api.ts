const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_KEY = 'super_secret_internal_key_change_in_production'

async function handleResponse(res: Response) {
  if (!res.ok) {
    const contentType = res.headers.get('content-type')
    let detail = 'Network error or server is down.'
    
    if (contentType?.includes('application/json')) {
      try {
        const errData = await res.json()
        detail = errData.detail || errData.message || detail
      } catch {
        const text = await res.text()
        detail = text || detail
      }
    } else {
      const text = await res.text()
      detail = text || detail
    }
    throw new Error(detail)
  }
  return res.json()
}

export async function publicPost(endpoint: string, payload: any, language?: string) {
  if (!navigator.onLine) throw new Error('You are offline. Please check your internet connection.')
  
  let body: string
  try {
    body = JSON.stringify({ ...payload, language })
  } catch (e) {
    throw new Error('Invalid request data')
  }
  
  const res = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body
  })
  return handleResponse(res)
}

export async function securePost(endpoint: string, payload?: any) {
  if (!navigator.onLine) throw new Error('System is offline.')
  
  let body: string | undefined
  if (payload) {
    try {
      body = JSON.stringify(payload)
    } catch (e) {
      throw new Error('Invalid request data')
    }
  }
  
  const res = await fetch(`${API_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-api-key': API_KEY },
    body
  })
  return handleResponse(res)
}

export async function secureGet(endpoint: string) {
  if (!navigator.onLine) throw new Error('System is offline.')
  const res = await fetch(`${API_URL}${endpoint}`, {
    method: 'GET',
    headers: { 'x-api-key': API_KEY }
  })
  return handleResponse(res)
}

export async function bookToken(data: { name: string; phone: string; doctor_id: string; symptom?: string }, language: string) {
  return publicPost('/book', data, language)
}

export async function checkStatus(phone: string) {
  return publicPost('/webhook/missed-call', { phone: `91${phone}` })
}

export async function addPatient(data: { name: string; phone: string }) {
  return securePost('/clerk/add', data)
}

export async function callNext() {
  return securePost('/clerk/call-next')
}

export async function assignDoctor(data: { registration_id: number; doctor_id: string }) {
  return securePost('/clerk/assign-doctor', data)
}

export async function doctorAction(action: string, data: { doctor_id: string; doctor_queue_id: number }) {
  return securePost(`/doctor/${action}`, data)
}

export interface SimulationStartResponse {
  simulation_id: string
  status: string
  message: string
}

export interface DisasterMetrics {
  patients_injected: number
  cases_detected: number
  confidence_percent: number
  sms_alerts_sent: number
  travel_prevented: number
  early_warning_hours: number
}

export interface SimulationStatusResponse {
  simulation_id: string
  status: string
  progress: number
  current_phase: string
  metrics: DisasterMetrics | null
  error: string | null
}

export async function startSimulation(scenario: string, count: number) {
  return securePost('/demo/start', { scenario, patient_count: count })
}

export async function getSimulationStatus(simId: string): Promise<SimulationStatusResponse> {
  return secureGet(`/demo/status/${simId}`)
}