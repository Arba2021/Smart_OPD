'use client'
import { DoctorMetrics } from '@/types'
import { Skeleton } from './ui/Skeleton'
import { Clock, Users, TrendingUp } from 'lucide-react'

interface MetricsWidgetProps {
  metrics: DoctorMetrics
  isLoading: boolean
}

export default function MetricsWidget({ metrics, isLoading }: MetricsWidgetProps) {
  if (isLoading) {
    return <div className="grid grid-cols-3 gap-4 mb-6"><Skeleton className="h-20 w-full" /><Skeleton className="h-20 w-full" /><Skeleton className="h-20 w-full" /></div>
  }

  const items = [
    { 
      label: 'Avg Consult', 
      value: metrics.avg_time, 
      icon: <Clock className="w-5 h-5 text-blue-600" />,
      color: 'bg-blue-50'
    },
    { 
      label: 'Remaining', 
      value: String(metrics.remaining), 
      icon: <Users className="w-5 h-5 text-emerald-600" />,
      color: 'bg-emerald-50'
    },
    { 
      label: 'ETA Finish', 
      value: metrics.eta, 
      icon: <TrendingUp className="w-5 h-5 text-purple-600" />,
      color: 'bg-purple-50'
    }
  ]

  return (
    <div className="grid grid-cols-3 gap-4 mb-8">
      {items.map(item => (
        <div key={item.label} className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-4 shadow-sm">
          <div className={`p-3 rounded-lg ${item.color}`}>
            {item.icon}
          </div>
          <div>
            <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">{item.label}</p>
            <p className="text-xl font-bold text-slate-900">{item.value}</p>
          </div>
        </div>
      ))}
    </div>
  )
}