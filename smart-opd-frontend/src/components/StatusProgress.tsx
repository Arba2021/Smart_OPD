import { Clock, Users, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react'

interface StatusProgressProps {
  token: string
  status: string
  waitMinutes: number
  patientsAhead: number
  triageColor?: string
  isLoading?: boolean
  language?: string
}

export default function StatusProgress({ 
  token, 
  status, 
  waitMinutes, 
  patientsAhead, 
  triageColor,
  isLoading 
}: StatusProgressProps) {
  const progress = patientsAhead <= 0 ? 100 : Math.max(0, 100 - (patientsAhead * 10))
  const isActive = status === 'CALLED' || status === 'IN_ROOM'
  const color = triageColor?.toUpperCase()

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-8 max-w-lg w-full mx-auto space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-slate-200 rounded w-1/3 mx-auto" />
          <div className="h-16 bg-slate-200 rounded w-2/3 mx-auto" />
          <div className="h-4 bg-slate-200 rounded w-full" />
          <div className="h-12 bg-slate-200 rounded w-full" />
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-8 max-w-lg w-full mx-auto space-y-8">
      <div className="text-center space-y-2">
        <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">Your Token</p>
        <p className="text-5xl font-extrabold tracking-tight text-slate-900">{token}</p>
        {color && color !== 'GREEN' && (
          <span className={`inline-flex items-center gap-1.5 mt-3 px-3 py-1 rounded-full text-xs font-bold text-white ${
            color === 'RED' ? 'bg-red-500' : 'bg-amber-500'
          }`}>
            <AlertTriangle className="w-3 h-3" />
            PRIORITY: {color}
          </span>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex justify-between text-sm font-medium text-slate-600">
          <span>{isActive ? 'Proceed to Doctor Room' : 'Waiting in Queue'}</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ease-out ${
              isActive ? 'bg-emerald-500' : 'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-center gap-3">
          <Users className="w-5 h-5 text-slate-400" />
          <div>
            <p className="text-xs text-slate-500 font-medium">Patients Ahead</p>
            <p className="text-xl font-bold text-slate-800">{patientsAhead}</p>
          </div>
        </div>
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex items-center gap-3">
          <Clock className="w-5 h-5 text-slate-400" />
          <div>
            <p className="text-xs text-slate-500 font-medium">Estimated Wait</p>
            <p className="text-xl font-bold text-slate-800">{waitMinutes} <span className="text-sm font-normal text-slate-500">min</span></p>
          </div>
        </div>
      </div>

      <div className={`flex items-start gap-3 p-4 rounded-xl border ${
        isActive ? 'bg-emerald-50 border-emerald-100' : 'bg-blue-50 border-blue-100'
      }`}>
        {isActive ? (
          <CheckCircle2 className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
        ) : (
          <ArrowRight className="w-5 h-5 text-blue-600 mt-0.5 shrink-0" />
        )}
        <p className={`text-sm font-medium ${isActive ? 'text-emerald-800' : 'text-blue-800'}`}>
          {isActive
            ? 'Please proceed to the doctor room immediately. Show your token at the entrance.'
            : 'Do not travel to the hospital yet. Wait for the "Start Walking" SMS alert.'}
        </p>
      </div>
    </div>
  )
}