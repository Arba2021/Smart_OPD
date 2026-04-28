'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'

interface AssignDoctorModalProps {
  isOpen: boolean
  onClose: () => void
  registrationId: number
  onAssignSuccess: () => void
}

const doctorOptions = [
  { value: '', label: 'Select Doctor Department' },
  { value: 'gen-001', label: 'Dr. Sharma (General)' },
  { value: 'orth-002', label: 'Dr. Patel (Ortho)' }
]

export default function AssignDoctorModal({ isOpen, onClose, registrationId, onAssignSuccess }: AssignDoctorModalProps) {
  const [doctorId, setDoctorId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  const handleAssign = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!doctorId) return
    setLoading(true)
    setError(null)
    try {
      const { assignDoctor } = await import('@/lib/api')
      await assignDoctor({ registration_id: registrationId, doctor_id: doctorId })
      onAssignSuccess()
      onClose()
      setDoctorId('')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-surface rounded-2xl border border-border shadow-xl w-full max-w-md p-6 space-y-4 mx-4">
        <div className="flex justify-between items-center">
          <h2 className="text-lg font-bold text-text">Assign to Doctor</h2>
          <button onClick={onClose} className="p-1 hover:bg-bg rounded-lg transition-colors">
            <svg className="h-5 w-5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {error && (
          <div className="bg-status-danger/5 border border-status-danger/20 rounded-xl p-3 text-sm text-status-danger font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleAssign} className="space-y-4">
          <Select
            label="Doctor / Department"
            options={doctorOptions}
            value={doctorId}
            onChange={e => setDoctorId(e.target.value)}
            required
          />
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">Cancel</Button>
            <Button type="submit" isLoading={loading} className="flex-1">Confirm Assign</Button>
          </div>
        </form>
      </div>
    </div>
  )
}