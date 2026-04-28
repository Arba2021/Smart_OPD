'use client'

import { useState, useEffect } from 'react'
import { Clock, Users, Calendar, AlertTriangle, CheckCircle, SkipForward, AlertOctagon, Loader2 } from 'lucide-react'
import { doctorAction, secureGet } from '@/lib/api'
import { DoctorQueuePatient, DoctorMetrics } from '@/types'

interface QueueData {
  active: DoctorQueuePatient | null
  upcoming: DoctorQueuePatient[]
  metrics: DoctorMetrics
  ai_warning?: string | null
}

export default function DoctorPage() {
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState(false)
  const [queueData, setQueueData] = useState<QueueData>({
    active: null,
    upcoming: [],
    metrics: { avg_time: '0 min', remaining: 0, eta: '--:--' }
  })
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const DOCTOR_ID = 'gen-001'

  const fetchQueueData = async () => {
    try {
      const data = await secureGet(`/doctor/queue?doctor_id=${DOCTOR_ID}`)
      setQueueData(data)
      setError(null)
    } catch (err: any) {
      setError(err.message || 'Failed to load queue data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchQueueData()
    const interval = setInterval(fetchQueueData, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleDoneAndNext = async () => {
    setProcessing(true)
    setSuccessMsg(null)
    try {
      if (queueData.active) {
        await doctorAction('done-next', {
          doctor_id: DOCTOR_ID,
          doctor_queue_id: queueData.active.id
        })
        setSuccessMsg('Patient completed. Next patient called.')
      } else {
        await doctorAction('call-next', { doctor_id: DOCTOR_ID })
        setSuccessMsg('Next patient called successfully.')
      }
      await fetchQueueData()
    } catch (err: any) {
      setError(err.message || 'Action failed')
    } finally {
      setProcessing(false)
    }
  }

  const handleSkip = async () => {
    if (!queueData.active) return
    setProcessing(true)
    setSuccessMsg(null)
    try {
      await doctorAction('skip', {
        doctor_id: DOCTOR_ID,
        doctor_queue_id: queueData.active.id
      })
      setSuccessMsg('Patient skipped.')
      await fetchQueueData()
    } catch (err: any) {
      setError(err.message || 'Failed to skip patient')
    } finally {
      setProcessing(false)
    }
  }

  const handleEmergency = async () => {
    setProcessing(true)
    setSuccessMsg(null)
    try {
      await doctorAction('emergency', { doctor_id: DOCTOR_ID, doctor_queue_id: 0 })
      setSuccessMsg('Emergency pause triggered. All waiting patients notified.')
      await fetchQueueData()
    } catch (err: any) {
      setError(err.message || 'Failed to trigger emergency')
    } finally {
      setProcessing(false)
    }
  }

  const getTriageColorClasses = (color?: string) => {
    switch (color?.toUpperCase()) {
      case 'RED': return 'bg-red-50 border-red-200 text-red-900'
      case 'YELLOW': return 'bg-amber-50 border-amber-200 text-amber-900'
      case 'GREEN': return 'bg-emerald-50 border-emerald-200 text-emerald-900'
      default: return 'bg-slate-50 border-slate-200 text-slate-900'
    }
  }

  const getTriageBadgeClasses = (color?: string) => {
    switch (color?.toUpperCase()) {
      case 'RED': return 'bg-red-500 text-white'
      case 'YELLOW': return 'bg-amber-500 text-white'
      case 'GREEN': return 'bg-emerald-500 text-white'
      default: return 'bg-slate-400 text-white'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dr. Sharma (General)</h1>
          <p className="text-slate-500">Active OPD Session</p>
        </div>
        <div className="flex gap-3">
          <div className="bg-white px-4 py-2 rounded-lg border border-slate-200 flex items-center gap-2">
            <Clock className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-medium text-slate-600">Avg: {queueData.metrics.avg_time}</span>
          </div>
          <div className="bg-white px-4 py-2 rounded-lg border border-slate-200 flex items-center gap-2">
            <Users className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-medium text-slate-600">Remaining: {queueData.metrics.remaining}</span>
          </div>
          <div className="bg-white px-4 py-2 rounded-lg border border-slate-200 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400" />
            <span className="text-sm font-medium text-slate-600">ETA: {queueData.metrics.eta}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="mb-6 bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-3 rounded-xl flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          <span>{successMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-bold text-slate-900">Current Patient</h2>
          </div>

          {queueData.active ? (
            <div className={`border-2 rounded-xl p-6 ${getTriageColorClasses(queueData.active.triage_color)}`}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-3xl font-black mb-1">{queueData.active.doctor_token}</p>
                  <p className="text-lg font-semibold">{queueData.active.name}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${getTriageBadgeClasses(queueData.active.triage_color)}`}>
                  PRIORITY: {queueData.active.triage_color}
                </span>
              </div>
              
              {queueData.active.symptom && (
                <div className="mb-4">
                  <p className="text-sm font-medium mb-1">Symptom</p>
                  <p className="text-sm opacity-90">{queueData.active.symptom}</p>
                </div>
              )}

              {queueData.ai_warning && (
                <div className="bg-white/50 border border-current rounded-lg p-3 mb-4">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                    <p className="text-sm">{queueData.ai_warning}</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center">
              <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Users className="w-8 h-8 text-slate-400" />
              </div>
              <p className="text-slate-600 font-medium mb-1">No Active Patient</p>
              <p className="text-sm text-slate-500">Click "Done & Next" to call the next patient.</p>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              onClick={handleDoneAndNext}
              disabled={processing}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold py-3 px-6 rounded-xl flex items-center justify-center gap-2 transition-colors"
            >
              {processing ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <CheckCircle className="w-5 h-5" />
              )}
              Done & Next
            </button>
            <button
              onClick={handleSkip}
              disabled={!queueData.active || processing}
              className="px-6 py-3 border border-slate-300 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl font-semibold flex items-center gap-2 transition-colors"
            >
              <SkipForward className="w-5 h-5" />
              Skip
            </button>
            <button
              onClick={handleEmergency}
              disabled={processing}
              className="px-6 py-3 bg-red-100 hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed text-red-700 rounded-xl font-semibold flex items-center gap-2 transition-colors"
            >
              <AlertOctagon className="w-5 h-5" />
              Emergency
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-5 h-5 text-slate-400" />
            <h2 className="text-lg font-bold text-slate-900">Upcoming Queue</h2>
          </div>

          {queueData.upcoming.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <p>No patients in queue</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
              {queueData.upcoming.map((patient) => (
                <div
                  key={patient.id}
                  className={`border-2 rounded-xl p-4 ${getTriageColorClasses(patient.triage_color)}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="font-bold text-lg">{patient.doctor_token}</p>
                      <p className="text-sm opacity-90">{patient.name}</p>
                    </div>
                    <div className={`w-3 h-3 rounded-full ${patient.status === 'CALLED' ? 'bg-blue-500 animate-pulse' : 'bg-emerald-500'}`} />
                  </div>
                  <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getTriageBadgeClasses(patient.triage_color)}`}>
                    {patient.triage_color}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}