'use client'
import { useState, useEffect, useRef } from 'react'
import { Shield } from 'lucide-react'
import ControlPanel from '@/components/ControlPanel'
import SimulationDashboard from '@/components/SimulationDashboard'
import MetricsDisplay from '@/components/MetricsDisplay'
import { startSimulation, getSimulationStatus, SimulationStatusResponse } from '@/lib/api'

export default function RadarPage() {
  const [simId, setSimId] = useState<string | null>(null)
  const [statusData, setStatusData] = useState<SimulationStatusResponse | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [patientCount, setPatientCount] = useState(500)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  const clearPoll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const startPolling = (id: string) => {
    clearPoll()
    pollRef.current = setInterval(async () => {
      try {
        const data = await getSimulationStatus(id)
        console.log('Simulation status:', data)
        setStatusData(data)
        
        if (data.status === 'CONTAINED' || data.status === 'FAILED') {
          setIsRunning(false)
          clearPoll()
        }
      } catch (err: any) {
        console.error('Status fetch error:', err)
        setError(err.message || 'Failed to fetch status')
        clearPoll()
        setIsRunning(false)
      }
    }, 2000)
  }

  const handleStart = async (count: number) => {
    setError(null)
    setIsRunning(true)
    setStatusData(null)
    setPatientCount(count)
    try {
      const res = await startSimulation('dengue', count)
      setSimId(res.simulation_id)
      startPolling(res.simulation_id)
    } catch (err: any) {
      setError(err.message || 'Failed to start simulation')
      setIsRunning(false)
    }
  }

  useEffect(() => {
    return () => clearPoll()
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6 flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-100 rounded-xl flex items-center justify-center">
          <Shield className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Epidemiological Radar</h1>
          <p className="text-slate-500">AI-powered outbreak detection & disaster prevention simulation</p>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-2">
          <Shield className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-1">
          <ControlPanel onStart={handleStart} isRunning={isRunning} />
        </div>
        <div className="lg:col-span-2">
          <SimulationDashboard
            status={statusData?.status || 'PENDING'}
            progress={statusData?.progress || 0}
            phase={statusData?.current_phase || 'PENDING'}
          />
        </div>
      </div>

      <MetricsDisplay metrics={statusData?.metrics || null} />
    </div>
  )
}