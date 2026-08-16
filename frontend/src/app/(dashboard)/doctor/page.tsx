"use client"

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { useAuth } from '@/components/auth/AuthProvider'
import { Users, Activity, AlertTriangle, FileText, CheckCircle, Copy, KeyRound } from 'lucide-react'
import Link from 'next/link'
import type { ClinicalAnalytics, DoctorPatientLink } from '@/lib/types'

export default function DoctorDashboard() {
  const { profile } = useAuth()
  const [analytics, setAnalytics] = useState<ClinicalAnalytics | null>(null)
  const [patients, setPatients] = useState<DoctorPatientLink[]>([])
  const [loading, setLoading] = useState(true)
  const [updatingLink, setUpdatingLink] = useState<string | null>(null)
  const [doctorCode, setDoctorCode] = useState('')

  const acceptPatient = async (linkId: string) => {
    setUpdatingLink(linkId)
    try {
      await api.updateLinkStatus(linkId, 'accepted')
      setPatients(current => current.map(link => link.id === linkId ? { ...link, status: 'accepted' } : link))
    } catch {
      alert('Could not accept this patient request. Please try again.')
    } finally {
      setUpdatingLink(null)
    }
  }

  useEffect(() => {
    async function load() {
      try {
        const [anData, patData, codeData] = await Promise.all([
          api.getClinicalAnalytics(),
          api.getPatients(),
          api.getDoctorCode()
        ])
        setAnalytics(anData)
        setPatients(patData || [])
        setDoctorCode(codeData.code)
      } catch (e) {
        console.error(e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return <div className="p-8 text-slate-400">Loading clinical portal...</div>
  }

  const acceptedPatients = patients.filter(p => p.status === 'accepted')
  const pendingRequests = patients.filter(p => p.status === 'pending')

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Overview</h1>
          <p className="text-slate-400 mt-1">Clinical prediction summary for {profile?.full_name}</p>
        </div>
        <Link href="/doctor/epidemiology" className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl transition-colors shadow-lg">
          <Activity className="w-4 h-4" />
          <span className="font-medium text-sm">Epidemiology Map</span>
        </Link>
      </header>

      <div className="bg-gradient-to-r from-emerald-500/10 to-blue-500/10 border border-emerald-500/20 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center gap-4">
        <div className="w-11 h-11 rounded-xl bg-white text-emerald-500 flex items-center justify-center"><KeyRound className="w-5 h-5" /></div>
        <div className="flex-1"><p className="text-sm font-semibold text-slate-200">Your Doctor Connection Code</p><p className="text-xs text-slate-500">Share this code with patients. Entering it connects them to your clinical workspace immediately.</p></div>
        <button onClick={() => navigator.clipboard.writeText(doctorCode)} className="px-4 py-2.5 bg-white border border-slate-800 rounded-xl flex items-center gap-2 font-mono font-bold text-slate-200"><span>{doctorCode || 'Loading...'}</span><Copy className="w-4 h-4" /></button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center shadow-lg">
          <div className="w-12 h-12 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center mr-4">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">Total Patients</p>
            <h3 className="text-2xl font-bold text-slate-100">{analytics?.totalPatients || 0}</h3>
          </div>
        </div>
        
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center shadow-lg">
          <div className="w-12 h-12 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center mr-4">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">Average Patient Risk</p>
            <h3 className="text-2xl font-bold text-slate-100">
              {analytics?.averageRiskAll ? (analytics.averageRiskAll * 100).toFixed(1) + '%' : 'N/A'}
            </h3>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center shadow-lg border-t-4 border-t-red-500">
          <div className="w-12 h-12 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center mr-4">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">High Risk Patients</p>
            <h3 className="text-2xl font-bold text-slate-100 text-red-400">{analytics?.highRiskPatients || 0}</h3>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Patient Table */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl shadow-lg overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex justify-between items-center">
            <h2 className="text-lg font-semibold text-slate-100">Patient Directory</h2>
            <Link href="/doctor/patients" className="text-sm text-blue-400 hover:text-blue-300">View All</Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-950/50 text-slate-400 text-xs uppercase tracking-wider">
                  <th className="p-4 font-medium">Patient Name</th>
                  <th className="p-4 font-medium">Status</th>
                  <th className="p-4 font-medium">Joined</th>
                  <th className="p-4 font-medium">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {acceptedPatients.length > 0 ? (
                  acceptedPatients.map(link => (
                    <tr key={link.id} className="hover:bg-slate-800/50 transition-colors">
                      <td className="p-4">
                        <div className="font-medium text-slate-200">{link.profiles.fullName}</div>
                        <div className="text-xs text-slate-500">BMI: {link.profiles.bmi || 'N/A'}</div>
                      </td>
                      <td className="p-4">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Active
                        </span>
                      </td>
                      <td className="p-4 text-slate-400 text-sm">
                        {new Date(link.createdAt).toLocaleDateString()}
                      </td>
                      <td className="p-4">
                        <Link href={`/doctor/patients/${link.patientId}`} className="text-blue-400 hover:text-blue-300 text-sm font-medium">
                          View Records
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-slate-500">No active patients.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pending Requests */}
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-lg">
            <div className="p-6 border-b border-slate-800">
              <h2 className="text-lg font-semibold text-slate-100 flex items-center">
                Pending Requests
                {pendingRequests.length > 0 && (
                  <span className="ml-2 bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full">
                    {pendingRequests.length}
                  </span>
                )}
              </h2>
            </div>
            <div className="p-4 divide-y divide-slate-800">
              {pendingRequests.length > 0 ? (
                pendingRequests.map(link => (
                  <div key={link.id} className="py-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-200">{link.profiles.fullName}</p>
                      <p className="text-xs text-slate-500">Requested {new Date(link.createdAt).toLocaleDateString()}</p>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => acceptPatient(link.id)} disabled={updatingLink === link.id} aria-label={`Accept ${link.profiles.fullName}`} className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 flex items-center justify-center transition-colors disabled:opacity-50">
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-slate-500 py-4 text-sm">
                  No new patient requests.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
