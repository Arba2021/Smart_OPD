'use client'
import { useState, useEffect } from 'react'
import { Users, Loader2 } from 'lucide-react'

interface QueueCountBadgeProps {
  doctorId: string
}

export default function QueueCountBadge({ doctorId }: QueueCountBadgeProps) {
  const [count, setCount] = useState<number | null>(null)

  useEffect(() => {
    const fetchCount = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/doctor/queue?doctor_id=${doctorId}`, {
          headers: { 'x-api-key': process.env.NEXT_PUBLIC_INTERNAL_API_KEY || '' }
        })
        if (res.ok) {
          const data = await res.json()
          setCount(data.metrics.remaining)
        }
      } catch {
        setCount(0)
      }
    }
    fetchCount()
    const interval = setInterval(fetchCount, 15000)
    return () => clearInterval(interval)
  }, [doctorId])

  if (count === null) return <div className="h-8 w-24 bg-slate-100 rounded animate-pulse" />

  return (
    <div className="inline-flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm">
      <Users className="w-4 h-4 text-slate-500" />
      <span className="text-sm font-medium text-slate-700">
        <span className="font-bold text-slate-900">{count}</span> patients in queue
      </span>
    </div>
  )
}