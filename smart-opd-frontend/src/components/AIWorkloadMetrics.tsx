'use client'
import { Activity, Clock, CheckCircle2 } from 'lucide-react'

interface AIWorkloadMetricsProps {
  totalProcessed: number
}

export default function AIWorkloadMetrics({ totalProcessed }: AIWorkloadMetricsProps) {
  const aiDrafted = Math.floor(totalProcessed * 0.4)
  const timeSaved = (aiDrafted * 2).toFixed(1) // Assume 2 mins saved per SMS

  return (
    <div className="flex items-center gap-4 bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-sm">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">AI Active</span>
      </div>
      <div className="h-4 w-px bg-slate-200" />
      <div className="flex items-center gap-1.5 text-xs text-slate-600">
        <CheckCircle2 className="w-3.5 h-3.5 text-blue-500" />
        <span><strong className="text-slate-900">{aiDrafted}</strong> SMS Sent</span>
      </div>
      <div className="h-4 w-px bg-slate-200" />
      <div className="flex items-center gap-1.5 text-xs text-slate-600">
        <Clock className="w-3.5 h-3.5 text-purple-500" />
        <span><strong className="text-slate-900">{timeSaved}m</strong> Staff Saved</span>
      </div>
    </div>
  )
}