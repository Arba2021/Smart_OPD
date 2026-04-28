'use client'
import { useState, useEffect } from 'react'
import { secureGet } from '@/lib/api'

export default function DisplayPage() {
  const [data, setData] = useState<any>(null)
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const fetchQueue = async () => {
      try {
        const res = await secureGet('/doctor/queue?doctor_id=gen-001')
        setData(res)
      } catch (err) {
        console.error("Display fetch failed")
      }
    }
    fetchQueue()
    const interval = setInterval(fetchQueue, 5000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col p-8 md:p-12 font-sans select-none overflow-hidden">
      {/* Header */}
      <div className="flex justify-between items-end border-b-2 border-slate-700 pb-6 mb-8">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">SMART OPD</h1>
          <p className="text-slate-400 text-sm mt-1">Intelligent Queue Management</p>
        </div>
        <div className="text-right">
          <p className="text-4xl md:text-5xl font-bold tabular-nums">
            {time.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col items-center justify-center gap-12">
        {data?.active ? (
          <>
            <div className="text-center">
              <p className="text-slate-400 text-xl tracking-widest mb-6 font-medium">NOW SERVING</p>
              <div className="bg-white text-slate-900 px-16 py-8 rounded-3xl shadow-2xl border-4 border-blue-500">
                <p className="text-8xl md:text-9xl font-black tracking-tight">
                  {data.active.doctor_token.split('-').pop()}
                </p>
              </div>
              <p className="text-3xl md:text-4xl font-bold mt-8 text-white">{data.active.name}</p>
              {data.active.triage_color === 'RED' && (
                <p className="text-red-400 text-lg mt-2 font-bold uppercase tracking-wider animate-pulse">Priority Alert</p>
              )}
            </div>

            <div className="flex gap-8">
              {data.upcoming.slice(0, 3).map((p: any, i: number) => (
                <div key={p.id} className="bg-slate-800 border border-slate-700 rounded-2xl px-8 py-6 min-w-[200px] text-center">
                  <p className="text-slate-500 text-xs uppercase tracking-wider mb-2">Up Next #{i + 1}</p>
                  <p className="text-4xl font-bold text-blue-400 mb-2">{p.doctor_token.split('-').pop()}</p>
                  <p className="text-slate-300 text-lg">{p.name}</p>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="text-center opacity-50">
            <p className="text-6xl font-bold text-slate-600 mb-4">00</p>
            <p className="text-2xl text-slate-500">Waiting for patients...</p>
          </div>
        )}
      </div>

      {/* Footer Metrics */}
      <div className="flex justify-between items-end border-t-2 border-slate-700 pt-6 mt-8 text-slate-400">
        <div className="flex gap-12">
          <div>
            <p className="text-xs uppercase tracking-wider mb-1">Queue Length</p>
            <p className="text-3xl font-bold text-white">{data?.metrics.remaining || 0}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wider mb-1">AI Avg Time</p>
            <p className="text-3xl font-bold text-emerald-400">{data?.metrics.avg_time || '0 min'}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs uppercase tracking-wider mb-1">Estimated Finish</p>
          <p className="text-3xl font-bold text-white">{data?.metrics.eta || '--:--'}</p>
        </div>
      </div>
    </div>
  )
}