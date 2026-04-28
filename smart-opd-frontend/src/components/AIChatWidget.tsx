'use client'
import { MessageSquare, X } from 'lucide-react'
import { useState } from 'react'

interface Message {
  role: string
  text: string
}

interface AIChatWidgetProps {
  messages: Message[]
}

export default function AIChatWidget({ messages }: AIChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-blue-600 text-white rounded-full shadow-lg flex items-center justify-center hover:bg-blue-700 transition-transform hover:scale-105"
      >
        <MessageSquare className="w-6 h-6" />
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col h-[400px]">
      <div className="bg-slate-900 p-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-white font-semibold text-sm">OPD Assistant</p>
            <p className="text-slate-400 text-xs">Online</p>
          </div>
        </div>
        <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-white">
          <X className="w-4 h-4" />
        </button>
      </div>
      
      <div className="flex-1 bg-slate-50 p-4 overflow-y-auto space-y-3">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center text-sm">
            <MessageSquare className="w-8 h-8 mb-2 opacity-20" />
            <p>No active conversations.</p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'system' ? 'justify-start' : 'justify-end'}`}>
              <div
                className={`
                  max-w-[85%] px-3 py-2 rounded-lg shadow-sm text-sm
                  ${msg.role === 'system' ? 'bg-white text-slate-800 border border-slate-100 rounded-tl-none' : 'bg-blue-600 text-white rounded-tr-none'}
                `}
              >
                {msg.text}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}