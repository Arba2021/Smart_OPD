// src/components/SymptomFeed.tsx
import { useState, useEffect, useRef } from 'react'
import { Activity, Clock } from 'lucide-react'

interface SymptomData {
  symptom: string
  time: string
}

export default function SymptomFeed() {
  const [symptoms, setSymptoms] = useState<SymptomData[]>([])
  const feedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchSymptoms = async () => {
      try {
        const res = await fetch('/admin/recent-symptoms')
        const data = await res.json()
        setSymptoms(data)
      } catch (err) {
        console.error(err)
      }
    }
    fetchSymptoms()
    const interval = setInterval(fetchSymptoms, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
      <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex items-center gap-2">
        <Activity className="w-4 h-4 text-blue-600" />
        <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Live Symptom Ingestion</h3>
      </div>
      
      <div ref={feedRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/50">
        {symptoms.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center">
            <Clock className="w-8 h-8 mb-2 opacity-20" />
            <p className="text-sm">Waiting for patient data...</p>
          </div>
        ) : (
          symptoms.map((s, i) => (
            <div key={i} className="bg-white border border-slate-100 rounded-lg p-3 flex items-center justify-between hover:border-slate-200 transition-colors">
              <p className="text-sm text-slate-800 font-medium truncate pr-4">"{s.symptom}"</p>
              <span className="text-xs text-slate-400 font-mono whitespace-nowrap">{s.time}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}