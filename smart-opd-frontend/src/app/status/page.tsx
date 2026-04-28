'use client'

import { useState } from 'react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import StatusProgress from '@/components/StatusProgress'
import StatusSmsDisplay from '@/components/StatusSmsDisplay'
import LanguageSelector from '@/components/LanguageSelector'
import { useLanguage } from '@/hooks/useLanguage'
import { checkStatus } from '@/lib/api'
import { StatusResponse, SmsLog } from '@/types'
import { Phone, AlertTriangle, Loader2 } from 'lucide-react'

export default function StatusPage() {
  const { language, t, loading: tLoading } = useLanguage()
  const [phone, setPhone] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusData, setStatusData] = useState<StatusResponse | null>(null)
  const [smsLogs, setSmsLogs] = useState<SmsLog[]>([])

  const checkTokenStatus = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setStatusData(null)
    setLoading(true)

    try {
      const data = await checkStatus(phone)
      setStatusData(data)

      // Use AI message if available, otherwise construct generic message
      let smsText = ''
      if (data.ai_message) {
        smsText = data.ai_message
      } else {
        smsText = `Token ${data.doctor_token} status: ${data.status}. 
Patients ahead: ${data.patients_ahead}. 
Estimated wait: ${data.wait_minutes} mins.
${data.triage_color === 'RED' ? 'Priority case.' : ''}`
      }

      setSmsLogs(prev => [{
        text: smsText.trim(),
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        type: 'info'
      }, ...prev])

    } catch (err: any) {
      const msg = err.message || 'Status check failed'
      if (msg.includes('NO_ACTIVE_TOKEN')) {
        setError(t?.('status.notFound') || 'No active token found for this number today.')
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setStatusData(null)
    setPhone('')
    setError(null)
  }

  if (tLoading) {
    return (
      <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center">
        <Loader2 className="animate-spin h-8 w-8 text-blue-600" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-[calc(100vh-4rem)]">
      <div className="flex flex-col lg:flex-row gap-8 h-full">
        <div className="flex-1 flex flex-col">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {t?.('status.title') || 'Check Token Status'}
              </h1>
              <p className="text-slate-500">
                {t?.('status.subtitle') || 'Enter your mobile number to track your token.'}
              </p>
            </div>
            <LanguageSelector />
          </div>

          <div className="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
            {!statusData ? (
              <div className="space-y-6">
                {error && (
                  <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl p-4 text-sm text-red-700 font-medium animate-fade-in">
                    <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold mb-1">Error</p>
                      <p>{error}</p>
                    </div>
                  </div>
                )}

                <form onSubmit={checkTokenStatus} className="space-y-4">
                  <Input
                    label={t?.('common.phone') || 'Mobile Number'}
                    type="tel"
                    placeholder={t?.('status.placeholder') || '10-digit number'}
                    value={phone}
                    onChange={e => setPhone(e.target.value.replace(/[^0-9]/g, ''))}
                    required
                    maxLength={10}
                  />

                  <Button 
                    type="submit" 
                    isLoading={loading} 
                    className="w-full h-12"
                    disabled={phone.length !== 10}
                  >
                    {loading ? 'Checking...' : (t?.('status.button') || 'Track Token')}
                  </Button>

                  {phone.length > 0 && phone.length < 10 && (
                    <p className="text-xs text-amber-600 text-center">
                      Please enter a valid 10-digit mobile number
                    </p>
                  )}
                </form>
              </div>
            ) : (
              <>
                <StatusProgress
                  token={statusData.doctor_token}
                  status={statusData.status}
                  waitMinutes={statusData.wait_minutes}
                  patientsAhead={statusData.patients_ahead}
                  triageColor={statusData.triage_color}
                  isLoading={false}
                  language={language}
                />

                <div className="text-center mt-6">
                  <Button 
                    variant="ghost" 
                    onClick={handleReset} 
                    className="text-slate-500 hover:text-slate-700"
                  >
                    {t?.('common.cancel') || 'Check another number'}
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="w-full lg:w-96 shrink-0 flex flex-col">
          <StatusSmsDisplay messages={smsLogs} />
        </div>
      </div>
    </div>
  )
}