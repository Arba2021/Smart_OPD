import Link from 'next/link'
import { Stethoscope, Clock, ShieldCheck, ChevronRight, Users } from 'lucide-react'

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      
      {/* Hero Section */}
      <div className="text-center mb-16">
        <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm font-medium mb-6">
          <ShieldCheck className="w-4 h-4" />
          <span>AI-Powered Queue Management</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900 mb-4">
          Smart OPD System
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto">
          Reduce waiting times, prevent unnecessary travel, and detect outbreaks early with intelligent patient flow control.
        </p>
      </div>

      {/* Action Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
        
        {/* Patient Booking */}
        <Link href="/book" className="group bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all">
          <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-6 text-blue-600 group-hover:scale-110 transition-transform">
            <Stethoscope className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Patient Booking</h3>
          <p className="text-slate-500 mb-6 text-sm">Get an AI-triaged token from home. Receive instructions on when to arrive.</p>
          <div className="flex items-center text-blue-600 font-medium text-sm">
            Book Appointment <ChevronRight className="w-4 h-4 ml-1" />
          </div>
        </Link>

        {/* Status Check */}
        <Link href="/status" className="group bg-white rounded-2xl p-8 shadow-sm border border-slate-200 hover:border-blue-300 hover:shadow-md transition-all">
          <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-6 text-slate-600 group-hover:scale-110 transition-transform">
            <Clock className="w-6 h-6" />
          </div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Check Token Status</h3>
          <p className="text-slate-500 mb-6 text-sm">View your position in the queue and estimated waiting time.</p>
          <div className="flex items-center text-slate-700 font-medium text-sm">
            Track Status <ChevronRight className="w-4 h-4 ml-1" />
          </div>
        </Link>

        {/* Staff Portal */}
        <div className="bg-white rounded-2xl p-8 shadow-sm border border-slate-200 flex flex-col justify-between">
          <div>
            <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center mb-6 text-emerald-600">
              <Users className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Staff Portal</h3>
            <p className="text-slate-500 mb-6 text-sm">Access for Clerks, Doctors, and TV Displays.</p>
          </div>
          <div className="flex gap-3">
            <Link href="/clerk" className="flex-1 text-center py-2.5 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition-colors">
              Clerk Login
            </Link>
            <Link href="/doctor" className="flex-1 text-center py-2.5 border border-slate-200 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50 transition-colors">
              Doctor
            </Link>
          </div>
        </div>
      </div>

    </div>
  )
}