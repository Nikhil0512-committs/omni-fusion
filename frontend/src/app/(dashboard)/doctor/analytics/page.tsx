"use client"

import { useState, useEffect } from "react"
import { Activity, BarChart, LineChart, PieChart, Users, AlertTriangle } from 'lucide-react'
import { api } from "@/lib/api"
import { ClinicalAnalytics } from "@/lib/types"
import { BarChart as ReBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import Link from "next/link"

export default function DoctorAnalyticsPage() {
  const [analytics, setAnalytics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const data = await api.getClinicalAnalytics()
        setAnalytics(data)
      } catch (err) {
        console.error("Failed to load analytics:", err)
      } finally {
        setLoading(false)
      }
    }
    loadAnalytics()
  }, [])

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Activity className="w-8 h-8 text-blue-500 animate-pulse" />
      </div>
    )
  }

  if (!analytics || analytics.totalPatients === 0) {
    return (
      <div className="p-8 max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Practice Analytics</h1>
          <p className="text-slate-400">View aggregate insights across your patient population.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-12 text-center flex flex-col items-center mt-12">
          <div className="w-20 h-20 bg-blue-500/10 rounded-full flex items-center justify-center mb-6">
            <BarChart className="w-10 h-10 text-blue-400" />
          </div>
          <h3 className="text-2xl font-semibold text-white mb-3">Not Enough Data</h3>
          <p className="text-slate-400 max-w-lg mb-8">
            You don't have any linked patients yet. Once your patients connect with you and perform assessments, aggregate insights will appear here.
          </p>
        </div>
      </div>
    )
  }

  const distributionData = [
    { name: 'Low Risk', count: analytics.riskDistribution?.low || 0, color: '#10b981' },
    { name: 'Medium Risk', count: analytics.riskDistribution?.medium || 0, color: '#f59e0b' },
    { name: 'High Risk', count: analytics.riskDistribution?.high || 0, color: '#ef4444' },
  ]

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Practice Analytics</h1>
        <p className="text-slate-400">Aggregate insights across your {analytics.totalPatients} connected patients.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center text-slate-400 mb-4">
            <Users className="w-5 h-5 mr-2 text-blue-400" />
            Total Patients
          </div>
          <div className="text-3xl font-bold text-white">{analytics.totalPatients}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center text-slate-400 mb-4">
            <Activity className="w-5 h-5 mr-2 text-emerald-400" />
            Avg Risk Score
          </div>
          <div className="text-3xl font-bold text-white">{(analytics.averageRiskAll * 100).toFixed(1)}%</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
          <div className="flex items-center text-slate-400 mb-4">
            <AlertTriangle className="w-5 h-5 mr-2 text-red-400" />
            High Risk Patients
          </div>
          <div className="text-3xl font-bold text-white">{analytics.highRiskPatients}</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Risk Distribution Chart */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center">
            <PieChart className="w-5 h-5 mr-2 text-blue-400" />
            Risk Distribution
          </h3>
          <div className="flex-1 min-h-[250px]">
            <ResponsiveContainer width="100%" height="100%">
              <ReBarChart data={distributionData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                  itemStyle={{ color: '#e2e8f0' }}
                  cursor={{ fill: '#1e293b', opacity: 0.4 }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={60}>
                  {distributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </ReBarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top High Risk Patients */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col">
          <h3 className="text-lg font-semibold text-white mb-6 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-red-400" />
            Top Highest Risk Patients
          </h3>
          <div className="flex-1 overflow-y-auto">
            {(!analytics.topPatients || analytics.topPatients.length === 0) ? (
              <div className="text-center text-slate-500 py-8">No assessment data available.</div>
            ) : (
              <div className="space-y-4">
                {analytics.topPatients.map((patient: any) => (
                  <Link 
                    href={`/doctor/patients/${patient.patientId}`}
                    key={patient.patientId}
                    className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/50 border border-transparent hover:border-slate-700/50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center font-bold text-slate-300 shrink-0">
                        {patient.name?.charAt(0) || 'P'}
                      </div>
                      <div className="truncate pr-4">
                        <div className="text-slate-200 font-medium truncate">{patient.name}</div>
                        <div className="text-xs text-slate-500 truncate">{patient.email}</div>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <div className={`font-bold ${patient.riskScore >= 0.20 ? 'text-red-400' : patient.riskScore >= 0.10 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {(patient.riskScore * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-slate-500">Risk Score</div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
