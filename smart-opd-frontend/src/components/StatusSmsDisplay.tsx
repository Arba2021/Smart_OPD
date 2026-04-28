'use client'

import { MessageSquare, Check, Clock } from 'lucide-react'
import { SmsLog } from '@/types'

interface StatusSmsDisplayProps {
  messages: SmsLog[]
  className?: string
}

export default function StatusSmsDisplay({ messages, className = '' }: StatusSmsDisplayProps) {
  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden flex flex-col h-full ${className}`}>
      <div className="bg-slate-900 p-4 flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
          <MessageSquare className="w-4 h-4 text-white" />
        </div>
        <div>
          <h3 className="text-white font-bold text-sm">SMS Simulator</h3>
          <p className="text-slate-400 text-xs">Live communication log</p>
        </div>
      </div>

      <div className="flex-1 bg-slate-50 p-4 overflow-y-auto space-y-4 max-h-[600px]">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center">
            <MessageSquare className="w-12 h-12 mb-3 opacity-20" />
            <p className="text-sm">No messages sent yet.</p>
            <p className="text-xs mt-1">Track a token to see SMS flow</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div 
              key={idx} 
              className={`bg-white p-4 rounded-xl shadow-sm border-l-4 animate-fade-in ${
                msg.type === 'error' ? 'border-red-500' : 
                msg.type === 'info' ? 'border-blue-500' : 
                'border-emerald-500'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-slate-400 font-mono">+91 98765 XXXXX</p>
                <div className="flex items-center gap-1 text-[10px] text-slate-400">
                  <Clock className="w-3 h-3" />
                  {msg.time}
                  <Check className="w-3 h-3 text-emerald-500" />
                </div>
              </div>
              <p className="text-sm text-slate-800 leading-relaxed whitespace-pre-wrap break-words">{msg.text}</p>
            </div>
          ))
        )}
      </div>

      <div className="p-3 bg-slate-100 border-t border-slate-200 text-center">
        <p className="text-[10px] text-slate-500 font-mono">MOCK DEVICE: DEMO MODE</p>
      </div>
    </div>
  )
}