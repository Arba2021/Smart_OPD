'use client'

import { Activity, CheckCircle2, AlertTriangle, Clock } from 'lucide-react'

interface DashboardProps {
  status: string
  progress: number
  phase: string
}

export default function SimulationDashboard({ status, progress, phase }: DashboardProps) {
  const getPhaseIcon = (p: string) => {
    switch (p) {
      case 'INJECTING': return <Activity className="w-5 h-5 text-blue-500" />
      case 'ANALYZING': return <Clock className="w-5 h-5 text-amber-500" />
      case 'DETECTED': return <AlertTriangle className="w-5 h-5 text-red-500" />
      case 'CONTAINED': return <CheckCircle2 className="w-5 h-5 text-emerald-500" />
      default: return <Activity className="w-5 h-5 text-slate-400" />
    }
  }

  const getPhaseColor = (p: string) => {
    switch (p) {
      case 'INJECTING': return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'ANALYZING': return 'text-amber-600 bg-amber-50 border-amber-200'
      case 'DETECTED': return 'text-red-600 bg-red-50 border-red-200'
      case 'CONTAINED': return 'text-emerald-600 bg-emerald-50 border-emerald-200'
      default: return 'text-slate-600 bg-slate-50 border-slate-200'
    }
  }

  const phases = ['PENDING', 'INJECTING', 'ANALYZING', 'DETECTED', 'CONTAINED']
  const currentIdx = phases.indexOf(status)

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          {getPhaseIcon(phase)}
          <h2 className="text-lg font-bold text-slate-900">Live Simulation Status</h2>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-bold border ${getPhaseColor(phase)}`}>
          {phase.replace('_', ' ')}
        </span>
      </div>

      <div className="mb-6">
        <div className="flex justify-between text-sm text-slate-600 mb-2">
          <span>Progress</span>
          <span className="font-bold">{progress}%</span>
        </div>
        <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ease-out ${
              status === 'CONTAINED' ? 'bg-emerald-500' : 
              status === 'DETECTED' ? 'bg-red-500' : 
              status === 'ANALYZING' ? 'bg-amber-500' : 'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-5 gap-2 mb-4">
        {phases.map((p, idx) => (
          <div key={p} className={`h-2 rounded-full transition-all ${idx <= currentIdx ? 'bg-blue-600' : 'bg-slate-200'}`} />
        ))}
      </div>

      <div className="text-center py-4">
        {status === 'PENDING' && <p className="text-slate-500">Ready to simulate</p>}
        {status === 'INJECTING' && <p className="text-blue-600 font-medium">Injecting patient records into OPD queue...</p>}
        {status === 'ANALYZING' && <p className="text-amber-600 font-medium">AI analyzing symptom clusters & patterns...</p>}
        {status === 'DETECTED' && <p className="text-red-600 font-bold">⚠️ Outbreak detected! Triggering prevention protocol...</p>}
        {status === 'CONTAINED' && <p className="text-emerald-600 font-bold">✅ Disaster contained. System secured.</p>}
        {status === 'FAILED' && <p className="text-red-600">Simulation failed. Check backend logs.</p>}
      </div>
    </div>
  )
}