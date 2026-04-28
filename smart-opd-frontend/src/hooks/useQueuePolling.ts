import { useState, useEffect, useCallback } from 'react'
import { secureGet } from '@/lib/api'

export function useClerkQueue() {
  const [queue, setQueue] = useState<any[]>([])
  const [isLoading, setIsLoading] = useState(true)

  const fetchQueue = useCallback(async () => {
    try {
      const data = await secureGet('/clerk/queue')
      setQueue(data)
    } catch (err) {
      console.error("Failed to fetch clerk queue")
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchQueue()
    const interval = setInterval(fetchQueue, 3000)
    return () => clearInterval(interval)
  }, [fetchQueue])

  return { queue, isLoading, refetch: fetchQueue }
}

export function useDoctorQueue(doctorId: string) {
  const [active, setActive] = useState<any>(null)
  const [upcoming, setUpcoming] = useState<any[]>([])
  const [metrics, setMetrics] = useState({ avg_time: '0 min', remaining: 0, eta: '--:--' })
  const [isLoading, setIsLoading] = useState(true)

  const fetchQueue = useCallback(async () => {
    try {
      const data = await secureGet(`/doctor/queue?doctor_id=${doctorId}`)
      setActive(data.active)
      setUpcoming(data.upcoming)
      setMetrics(data.metrics)
    } catch (err) {
      console.error("Failed to fetch doctor queue")
    } finally {
      setIsLoading(false)
    }
  }, [doctorId])

  useEffect(() => {
    fetchQueue()
    const interval = setInterval(fetchQueue, 3000)
    return () => clearInterval(interval)
  }, [fetchQueue])

  return { active, upcoming, metrics, isLoading, refetch: fetchQueue }
}