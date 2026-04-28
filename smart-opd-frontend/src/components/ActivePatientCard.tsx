import { DoctorQueuePatient } from '@/types'
import { AlertTriangle, Activity, User } from 'lucide-react'
import { Skeleton } from './ui/Skeleton'

interface ActivePatientCardProps {
  patient: DoctorQueuePatient | null
  isLoading: boolean
}

export function ActivePatientCard({ patient, isLoading }: ActivePatientCardProps) {
  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><Skeleton className="h-24 w-64" /></div>
  }

  if (!patient) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center border-2 border-dashed border-slate-200 rounded-xl">
        <User className="w-12 h-12 text-slate-300 mb-3" />
        <p className="text-slate-500 font-medium">No Active Patient</p>
        <p className="text-slate-400 text-sm mt-1">Click "Done & Next" to call the next patient.</p>
      </div>
    )
  }

  const triageColor = patient.triage_color?.toUpperCase()
  const getTriageStyles = () => {
    if (triageColor === 'RED') return 'bg-red-50 border-red-200 text-red-700'
    if (triageColor === 'YELLOW') return 'bg-amber-50 border-amber-200 text-amber-700'
    return 'bg-emerald-50 border-emerald-200 text-emerald-700'
  }

  return (
    <div className="flex flex-col items-center text-center space-y-6">
      
      <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-bold tracking-wider ${getTriageStyles()}`}>
        <Activity className="w-3 h-3" />
        TRIAGE: {triageColor}
      </div>

      <div>
        <p className="text-sm font-medium text-slate-400 uppercase tracking-widest mb-1">Token Number</p>
        <p className="text-7xl md:text-8xl font-black text-slate-900 tracking-tight font-mono">
          {patient.doctor_token.split('-').pop()}
        </p>
      </div>

      <div className="space-y-2 max-w-md">
        <h2 className="text-3xl font-bold text-slate-800">{patient.name}</h2>
        {patient.symptom && (
          <p className="text-slate-500 flex items-center justify-center gap-2">
            <AlertTriangle className="w-4 h-4 text-slate-400" />
            Symptom: <span className="font-medium text-slate-700">{patient.symptom}</span>
          </p>
        )}
      </div>

    </div>
  )
}