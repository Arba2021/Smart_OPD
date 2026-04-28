// src/components/RegistrationList.tsx
import { RegistrationPatient } from '@/types'
import { Skeleton } from './ui/Skeleton'
import { Users, Clock } from 'lucide-react'

interface RegistrationListProps {
  patients: RegistrationPatient[]
  isLoading: boolean
}

export default function RegistrationList({ patients, isLoading }: RegistrationListProps) {
  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    )
  }

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden h-full flex flex-col">
      <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-slate-500" />
          <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Registration Queue</h2>
        </div>
        <span className="text-xs font-bold text-slate-500 bg-white px-2.5 py-1 rounded-md border border-slate-200">
          {patients.length} Active
        </span>
      </div>
      
      <div className="overflow-y-auto flex-1">
        {patients.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-slate-400">
            <Clock className="w-10 h-10 mb-3 opacity-20" />
            <p className="text-sm font-medium">No patients waiting</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-slate-50 sticky top-0 z-10">
              <tr className="text-left text-xs font-bold text-slate-500 uppercase tracking-wider">
                <th className="px-6 py-3">Token</th>
                <th className="px-6 py-3">Patient Name</th>
                <th className="px-6 py-3">Phone</th>
                <th className="px-6 py-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {patients.map(p => (
                <tr key={p.id} className="hover:bg-blue-50/40 transition-colors border-l-4 border-l-transparent hover:border-l-blue-500">
                  <td className="px-6 py-4 font-mono font-bold text-slate-800">{p.reg_token}</td>
                  <td className="px-6 py-4 text-slate-700 font-medium">{p.name}</td>
                  <td className="px-6 py-4 text-slate-500 font-mono">{p.phone}</td>
                  <td className="px-6 py-4 text-right">
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-md ${
                      p.status === 'REG_WAITING' ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-blue-700'
                    }`}>
                      {p.status.replace('REG_', '')}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}