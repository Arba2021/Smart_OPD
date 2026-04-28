'use client'
import { useEffect } from 'react'
import { Bot, X } from 'lucide-react'

interface AIToastProps {
  message: string | null
  onDone: () => void
}

export default function AIToast({ message, onDone }: AIToastProps) {
  useEffect(() => {
    if (!message) return
    const timer = setTimeout(() => {
      onDone()
    }, 4000)
    return () => clearTimeout(timer)
  }, [message, onDone])

  if (!message) return null

  return (
    <div className="fixed top-24 left-1/2 -translate-x-1/2 z-50 animate-slide-down">
      <div className="bg-slate-900 text-white px-5 py-4 rounded-xl shadow-2xl flex items-center gap-4 max-w-md w-full border border-slate-700">
        <div className="shrink-0 w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
          <Bot className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold text-blue-300 uppercase tracking-wider mb-0.5">AI Notification</p>
          <p className="text-sm text-slate-200 truncate">{message}</p>
        </div>
        <button onClick={onDone} className="text-slate-400 hover:text-white transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}