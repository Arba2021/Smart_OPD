'use client'
import { useState } from 'react'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { bookToken } from '@/lib/api'
import { Language } from '@/types'
import { User, Phone, Stethoscope, ShieldCheck, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'

const doctorOptions = [
  { value: 'gen-001', label: 'Dr. Sharma (General)' },
  { value: 'orth-002', label: 'Dr. Patel (Ortho)' }
]

const languageOptions = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'हिन्दी (Hindi)' },
  { value: 'te', label: 'తెలుగు (Telugu)' },
  { value: 'ta', label: 'தமிழ் (Tamil)' },
  { value: 'bn', label: 'বাংলা (Bengali)' },
  { value: 'mr', label: 'मराठी (Marathi)' }
]

interface PatientBookingFormProps {
  onCutoffTriggered: (err: any) => void
  onSuccess?: (message: string, data: any) => void
  onLoadingChange?: (loading: boolean) => void
  onBookAnother?: () => void
}

export default function PatientBookingForm({
  onCutoffTriggered,
  onSuccess,
  onLoadingChange,
  onBookAnother
}: PatientBookingFormProps) {
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [symptom, setSymptom] = useState('')
  const [doctorId, setDoctorId] = useState('gen-001')
  const [language, setLanguage] = useState<Language>('en')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const errors: Record<string, string> = {}
    if (!name.trim() || name.trim().length < 2) errors.name = 'Name must be at least 2 characters'
    if (!/^[6-9]\d{9}$/.test(phone)) errors.phone = 'Enter a valid 10-digit Indian mobile number'
    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    setLoading(true)
    setResult(null)
    onLoadingChange?.(true)

    try {
      const data = await bookToken({ name, phone, doctor_id: doctorId, symptom }, language)
      setResult(data)
      
      // Call parent success handler with both message and full data
      if (onSuccess) {
        onSuccess(data.ai_message, data)
      }
    } catch (err: any) {
      onCutoffTriggered(err)
    } finally {
      setLoading(false)
      onLoadingChange?.(false)
    }
  }

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/\D/g, '').slice(0, 10)
    setPhone(value)
    if (/^[6-9]\d{9}$/.test(value)) {
      setValidationErrors(prev => ({ ...prev, phone: '' }))
    }
  }

  const handleBookAnother = () => {
    setResult(null)
    setName('')
    setPhone('')
    setSymptom('')
    setValidationErrors({})
    onBookAnother?.()
  }

  if (result) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center space-y-6 py-8">
        <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center">
          <ShieldCheck className="w-8 h-8 text-emerald-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Token Confirmed</h2>
          <p className="text-slate-500 mt-1">Your appointment is booked.</p>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded-xl p-6 w-full max-w-sm">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Your Token</p>
          <p className="text-4xl font-black text-blue-600 tracking-wider font-mono">{result.doctor_token}</p>
          
          <div className="mt-4 bg-white p-3 rounded border border-slate-100">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">SMS Message</p>
            <p className="text-sm text-slate-700 leading-relaxed break-words whitespace-pre-wrap italic">
              "{result.ai_message}"
            </p>
          </div>
        </div>

        <Button
          onClick={handleBookAnother}
          variant="outline"
          className="mt-4"
        >
          Book Another Patient
        </Button>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-xl mx-auto space-y-5">
      <Select
        label="Select Doctor"
        options={doctorOptions}
        value={doctorId}
        onChange={e => setDoctorId(e.target.value)}
      />
      
      <Select
        label="Preferred Language"
        options={languageOptions}
        value={language}
        onChange={e => setLanguage(e.target.value as Language)}
      />

      <div className="space-y-1.5">
        <Input
          label="Patient Name"
          value={name}
          onChange={e => {
            setName(e.target.value)
            if (e.target.value.trim().length >= 2) {
              setValidationErrors(prev => ({ ...prev, name: '' }))
            }
          }}
          required
          placeholder="Full Name"
          error={validationErrors.name}
        />
      </div>

      <div className="space-y-1.5">
        <Input
          label="Mobile Number"
          type="tel"
          value={phone}
          onChange={handlePhoneChange}
          required
          placeholder="10-digit number"
          maxLength={10}
          hint={phone.length === 10 && /^[6-9]\d{9}$/.test(phone) ? (
            "Valid number format"
          ) : phone.length > 0 ? (
            "Must start with 6-9 and be 10 digits"
          ) : "We will send you an SMS in your selected language."}
          error={validationErrors.phone}
        />
      </div>

      <Input
        label="Symptom (Optional)"
        value={symptom}
        onChange={e => setSymptom(e.target.value)}
        placeholder="e.g. Fever, Joint Pain"
      />

      <Button
        type="submit"
        isLoading={loading}
        className="w-full mt-2 h-12 text-lg"
        disabled={loading || !name.trim() || !/^[6-9]\d{9}$/.test(phone)}
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Processing...
          </>
        ) : (
          'Get Token'
        )}
      </Button>
    </form>
  )
}