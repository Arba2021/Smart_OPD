'use client'
import { useState } from 'react'
import { Play, Loader2, AlertTriangle } from 'lucide-react'

interface ControlPanelProps {
  onStart: (count: number) => void
  isRunning: boolean
}

export default function ControlPanel({ onStart, isRunning }: ControlPanelProps) {
  const [scenario, setScenario] = useState('dengue')
  const [count, setCount] = useState(500)

  const handleStart = () => {
    onStart(count)
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Play className="w-5 h-5 text-blue-600" />
        <h2 className="text-lg font-bold text-slate-900">Simulation Control</h2>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Select Scenario
          </label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            disabled={isRunning}
            className="w-full px-4 py-2.5 rounded-xl border border-slate-300 bg-white text-slate-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value="dengue">Dengue Outbreak (High Severity)</option>
            <option value="viral_fever">Viral Fever Cluster (Medium Severity)</option>
            <option value="cholera">Cholera Spread (Critical Severity)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1.5">
            Patient Volume: <span className="text-blue-600 font-bold">{count}</span>
          </label>
          <input
            type="range"
            min="100"
            max="1000"
            step="50"
            value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            disabled={isRunning}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600 disabled:opacity-50"
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>100</span>
            <span>1000</span>
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={isRunning}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-bold py-3 px-6 rounded-xl flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Simulation Running...
            </>
          ) : (
            <>
              <Play className="w-5 h-5" />
              Start Disaster Simulation
            </>
          )}
        </button>

        {isRunning && (
          <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
            <AlertTriangle className="w-4 h-4" />
            <span>AI is processing massive symptom clusters. Results appear below.</span>
          </div>
        )}
      </div>
    </div>
  )
}