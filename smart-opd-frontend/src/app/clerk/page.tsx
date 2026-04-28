'use client'
import { useState, useEffect } from 'react'
import { Input } from '@/components/ui/Input'
import RegistrationList from '@/components/RegistrationList'
import AssignDoctorModal from './AssignDoctorModal'
import { useClerkQueue } from '@/hooks/useQueuePolling'
import { addPatient, callNext } from '@/lib/api'
import { Plus, PhoneCall, ArrowRight, Loader2 } from 'lucide-react'

export default function ClerkDashboard() {
  const { queue, isLoading, refetch } = useClerkQueue()
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [activePatient, setActivePatient] = useState<any>(null)
  const [actionLoading, setActionLoading] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)

  const handleAddPatient = async (e: React.FormEvent) => {
    e.preventDefault()
    setActionLoading('add')
    try {
      await addPatient({ name, phone })
      setName(''); setPhone('')
      await refetch()
    } catch (err) {
      alert('Failed to add patient')
    } finally {
      setActionLoading('')
    }
  }

  const handleCallNext = async () => {
    setActionLoading('call')
    try {
      const res = await callNext()
      setActivePatient(res)
      await refetch()
    } catch (err) {
      alert('Queue is empty')
    } finally {
      setActionLoading('')
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col overflow-hidden bg-slate-50">
      <div className="flex flex-1 overflow-hidden">
        
        {/* Sidebar Actions */}
        <aside className="w-full md:w-96 bg-white border-r border-slate-200 flex flex-col shrink-0">
          <div className="p-6 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 mb-1">Clerk Actions</h2>
            <p className="text-sm text-slate-500">Manage registration queue</p>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <form onSubmit={handleAddPatient} className="space-y-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide flex items-center gap-2">
                <Plus className="w-4 h-4" /> New Registration
              </h3>
              <Input
                placeholder="Phone Number"
                type="tel"
                value={phone}
                onChange={e => setPhone(e.target.value.replace(/[^0-9]/g, ''))}
                required
                maxLength={10}
              />
              <Input
                placeholder="Patient Name"
                value={name}
                onChange={e => setName(e.target.value)}
                required
              />
              <button
                type="submit"
                disabled={actionLoading === 'add'}
                className="w-full bg-slate-900 text-white font-medium py-2.5 rounded-lg text-sm hover:bg-slate-800 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
              >
                {actionLoading === 'add' && <Loader2 className="w-4 h-4 animate-spin" />}
                Add to Queue
              </button>
            </form>

            <div className="border-t border-slate-100 pt-6">
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wide mb-4 flex items-center gap-2">
                <PhoneCall className="w-4 h-4" /> Queue Management
              </h3>
              
              <button
                onClick={handleCallNext}
                disabled={actionLoading === 'call'}
                className="w-full bg-blue-600 text-white font-medium py-3 rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
              >
                {actionLoading === 'call' ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                Call Next Patient
              </button>
              <p className="text-xs text-slate-400 text-center mt-2 font-mono">Shortcut: [ENTER]</p>
            </div>

            {activePatient && (
              <div className="mt-6 bg-blue-50 border border-blue-100 rounded-xl p-5 animate-fade-in">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-bold text-blue-600 uppercase">Currently Calling</span>
                </div>
                <p className="text-3xl font-black text-slate-900 font-mono mb-1">{activePatient.reg_token}</p>
                <p className="text-lg font-semibold text-slate-800">{activePatient.name}</p>
                <p className="text-sm text-slate-500 font-mono mb-4">{activePatient.phone}</p>
                <button
                  onClick={() => setIsModalOpen(true)}
                  className="w-full bg-white border border-blue-200 text-blue-700 font-bold py-2 rounded-lg text-sm hover:bg-blue-50 transition-colors"
                >
                  Assign to Doctor
                </button>
              </div>
            )}
          </div>
        </aside>

        {/* Main Queue Area */}
        <main className="flex-1 overflow-hidden flex flex-col">
          <div className="p-6 bg-white border-b border-slate-200 flex justify-between items-center">
            <h2 className="text-lg font-bold text-slate-900">Registration Queue</h2>
            <span className="bg-slate-100 text-slate-600 px-3 py-1 rounded-full text-xs font-bold">{queue.length} Waiting</span>
          </div>
          <div className="flex-1 overflow-auto p-6 bg-slate-50">
            <RegistrationList patients={queue} isLoading={isLoading} />
          </div>
        </main>
      </div>

      <AssignDoctorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        registrationId={activePatient?.id || 0}
        onAssignSuccess={() => { setActivePatient(null); refetch() }}
      />
    </div>
  )
}