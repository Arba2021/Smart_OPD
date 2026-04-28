'use client'
import { MessageSquare, Check } from 'lucide-react'

interface SmsSimulatorProps {
  message: string | null
  onClose: () => void
}

export default function SmsSimulator({ message, onClose }: SmsSimulatorProps) {
  // This component is primarily used as a standalone modal in other flows
  // but for the /book page, we use the inline log in page.tsx.
  // Keeping this for /patient or status usage.
  
  if (!message) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden animate-fade-in">
        <div className="bg-slate-900 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-500" />
            <h3 className="text-white font-bold">SMS Received</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <div className="p-6 bg-slate-50">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 relative">
            <p className="text-xs text-slate-400 font-mono mb-1">+91 98765 XXXXX</p>
            <p className="text-sm text-slate-800 leading-relaxed">{message}</p>
            <div className="flex items-center justify-end gap-1 mt-2">
              <span className="text-[10px] text-slate-400">Just now</span>
              <Check className="w-3 h-3 text-blue-500" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}