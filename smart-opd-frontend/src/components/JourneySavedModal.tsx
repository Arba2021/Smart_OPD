'use client'

import { MapPinOff, ShieldCheck, Banknote, X } from 'lucide-react'

interface JourneySavedModalProps {
  data: { patient: string; ai_message: string } | null
  onClose: () => void
}

export default function JourneySavedModal({ data, onClose }: JourneySavedModalProps) {
  if (!data) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 bg-slate-100 hover:bg-slate-200 rounded-full transition-colors z-10"
          aria-label="Close modal"
        >
          <X className="w-4 h-4 text-slate-600" />
        </button>

        <div className="bg-gradient-to-r from-emerald-500 to-teal-600 p-8 text-center text-white">
          <div className="mx-auto w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mb-4 ring-4 ring-white/30">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Journey Prevented</h2>
          <p className="text-emerald-100 mt-2 text-sm font-medium">AI Capacity Protection Activated</p>
        </div>

        <div className="p-6 space-y-6">
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-center">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Patient</p>
            <p className="text-lg font-bold text-slate-800">{data.patient}</p>
          </div>

          <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                <MapPinOff className="w-4 h-4" />
              </div>
              <p className="text-sm font-bold text-blue-800">AI Advisory Message</p>
            </div>
            <p className="text-slate-700 text-sm leading-relaxed break-words whitespace-pre-wrap italic">"{data.ai_message}"</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-emerald-50 rounded-xl p-4 text-center border border-emerald-100">
              <Banknote className="w-5 h-5 text-emerald-600 mx-auto mb-2" />
              <p className="text-xs text-emerald-700 font-medium">Wage Saved</p>
              <p className="text-xl font-extrabold text-emerald-800">₹1,000</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 text-center border border-slate-200">
              <MapPinOff className="w-5 h-5 text-slate-600 mx-auto mb-2" />
              <p className="text-xs text-slate-500 font-medium">Travel Prevented</p>
              <p className="text-xl font-extrabold text-slate-700">1 Trip</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="w-full bg-slate-900 text-white font-bold py-3 rounded-xl hover:bg-slate-800 transition-all active:scale-[0.98]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}