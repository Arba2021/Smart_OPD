'use client'
import { useState } from 'react'
import PatientBookingForm from '@/components/PatientBookingForm'
import JourneySavedModal from '@/components/JourneySavedModal'
import { Loader2 } from 'lucide-react'

export default function BookPage() {
  const [cutoffData, setCutoffData] = useState<{ patient: string; ai_message: string } | null>(null)
  const [smsLogs, setSmsLogs] = useState<string[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [lastBookingData, setLastBookingData] = useState<any>(null)

  const handleBookingSuccess = (message: string, data: any) => {
    // Add SMS to logs
    setSmsLogs(prev => [message, ...prev].slice(0, 50))
    setLastBookingData(data)
  }

  const handleBookingError = (err: any) => {
    const detail = err?.detail
    if (detail && typeof detail === 'object' && detail.type === 'CUTOFF') {
      setCutoffData({
        patient: detail.patient || 'Patient',
        ai_message: detail.ai_message || 'Queue is full. Please try again tomorrow.'
      })
      setSmsLogs(prev => [detail.ai_message, ...prev].slice(0, 50))
    }
  }

  const handleClearLogs = () => {
    setSmsLogs([])
  }

  const handleBookAnother = () => {
    setLastBookingData(null)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col lg:flex-row gap-8">
        <div className="flex-1">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-slate-900">Book Appointment</h1>
            <p className="text-slate-500">Enter patient details to generate a queue token.</p>
          </div>
          
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
            <PatientBookingForm
              onCutoffTriggered={handleBookingError}
              onSuccess={handleBookingSuccess}
              onLoadingChange={setIsProcessing}
              onBookAnother={handleBookAnother}
            />
          </div>
        </div>

        <div className="w-full lg:w-96 shrink-0">
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-[600px]">
            <div className="bg-slate-900 p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-white font-bold text-sm">SMS Simulator</h3>
                  <p className="text-slate-400 text-xs">Live communication log</p>
                </div>
              </div>
              {smsLogs.length > 0 && (
                <button
                  onClick={handleClearLogs}
                  className="text-xs text-slate-400 hover:text-white transition-colors"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="flex-1 bg-slate-50 p-4 overflow-y-auto space-y-4">
              {isProcessing && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                  <span className="ml-2 text-sm text-slate-600">Processing...</span>
                </div>
              )}
              
              {smsLogs.length === 0 && !isProcessing ? (
                <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center">
                  <svg className="w-12 h-12 mb-3 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                  <p className="text-sm">No messages sent yet.</p>
                  <p className="text-xs mt-1 opacity-75">Book an appointment to see SMS</p>
                </div>
              ) : (
                smsLogs.map((msg, idx) => (
                  <div
                    key={idx}
                    className="bg-white p-3 rounded-lg shadow-sm border border-slate-200 animate-fade-in"
                  >
                    <p className="text-xs text-slate-400 font-mono mb-1">+91 98765 XXXXX</p>
                    <p className="text-sm text-slate-800 leading-relaxed break-words whitespace-pre-wrap">{msg}</p>
                    <p className="text-[10px] text-slate-400 text-right mt-1">Just now</p>
                  </div>
                ))
              )}
            </div>

            <div className="p-3 bg-slate-100 border-t border-slate-200 text-center">
              <p className="text-[10px] text-slate-500 font-mono">MOCK DEVICE: SIMULATOR MODE</p>
            </div>
          </div>
        </div>
      </div>

      <JourneySavedModal data={cutoffData} onClose={() => setCutoffData(null)} />
    </div>
  )
}