'use client'
import { DoctorQueuePatient } from '@/types'
import { Skeleton } from './ui/Skeleton'
import { Clock, User } from 'lucide-react'

interface DoctorQueueListProps {
  patients: DoctorQueuePatient[]
  isLoading: boolean
}

export default function DoctorQueueList({ patients, isLoading }: DoctorQueueListProps) {
  if (isLoading) {
    return <div className="flex gap-4"><Skeleton className="h-16 w-48" /><Skeleton className="h-16 w-48" /></div>
  }

  if (patients.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-slate-400 border-2 border-dashed border-slate-200 rounded-xl">
        <div className="text-center">
          <User className="w-6 h-6 mx-auto mb-2 opacity-50" />
          <p className="text-sm font-medium">Queue is empty</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-4 h-4 text-slate-500" />
        <span className="text-sm font-bold text-slate-700 uppercase tracking-wide">Upcoming</span>
      </div>
      
      <div className="space-y-3">
        {patients.slice(0, 5).map((p, i) => (
          <div 
            key={p.id} 
            className={`
              flex items-center justify-between p-4 rounded-xl border transition-all
              ${p.triage_color === 'RED' ? 'bg-red-50 border-red-100' : 'bg-white border-slate-100 hover:border-blue-200'}
            `}
          >
            <div className="flex items-center gap-4">
              <div className="flex flex-col items-center justify-center w-10 h-10 rounded-lg bg-slate-100 text-slate-600 font-bold text-sm shrink-0">
                {i + 1}
              </div>
              <div>
                <p className={`font-bold text-slate-900 ${p.triage_color === 'RED' ? 'text-red-700' : ''}`}>
                  {p.name}
                </p>
                <p className="text-xs text-slate-500 font-mono">{p.doctor_token}</p>
              </div>
            </div>
            <div className={`
              px-2 py-1 rounded text-xs font-bold uppercase
              ${p.triage_color === 'RED' ? 'bg-red-100 text-red-700' : 
                p.triage_color === 'YELLOW' ? 'bg-amber-100 text-amber-700' : 
                'bg-slate-100 text-slate-600'}
            `}>
              {p.triage_color || 'WAIT'}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}