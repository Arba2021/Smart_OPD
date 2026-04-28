'use client'
import { Users, ShieldCheck, Clock, MessageSquare, MapPinOff, TrendingUp } from 'lucide-react'

interface MetricsDisplayProps {
  metrics: {
    patients_injected: number
    cases_detected: number
    confidence_percent: number
    sms_alerts_sent: number
    travel_prevented: number
    early_warning_hours: number
  } | null
}

export default function MetricsDisplay({ metrics }: MetricsDisplayProps) {
  if (!metrics) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm text-center py-12">
        <TrendingUp className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="text-slate-500">Metrics will appear after simulation completes</p>
      </div>
    )
  }

  const cards = [
    { label: 'Patients Injected', value: metrics.patients_injected, icon: Users, color: 'text-blue-600 bg-blue-50' },
    { label: 'Cases Detected', value: metrics.cases_detected, icon: ShieldCheck, color: 'text-red-600 bg-red-50' },
    { label: 'AI Confidence', value: `${metrics.confidence_percent}%`, icon: TrendingUp, color: 'text-amber-600 bg-amber-50' },
    { label: 'SMS Alerts Sent', value: metrics.sms_alerts_sent, icon: MessageSquare, color: 'text-emerald-600 bg-emerald-50' },
    { label: 'Travel Prevented', value: metrics.travel_prevented, icon: MapPinOff, color: 'text-purple-600 bg-purple-50' },
    { label: 'Early Warning', value: `${metrics.early_warning_hours}h`, icon: Clock, color: 'text-indigo-600 bg-indigo-50' }
  ]

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-blue-600" />
        Impact Metrics
      </h2>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {cards.map((card, idx) => (
          <div key={idx} className={`${card.color} rounded-xl p-4 text-center transition-all hover:scale-[1.02]`}>
            <card.icon className="w-6 h-6 mx-auto mb-2" />
            <p className="text-2xl font-black">{card.value}</p>
            <p className="text-xs font-medium opacity-80 mt-1">{card.label}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 p-3 bg-slate-50 rounded-lg text-center text-sm text-slate-600">
        💡 <strong>Disaster Prevention Score:</strong> System detected outbreak in real-time.
        Prevented {metrics.travel_prevented} unnecessary hospital visits, saving ~₹{(metrics.travel_prevented * 1000).toLocaleString()} in daily wages.
      </div>
    </div>
  )
}