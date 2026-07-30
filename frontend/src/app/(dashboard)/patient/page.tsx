"use client"

import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { useAuth } from '@/components/auth/AuthProvider'
import { Activity, Heart, AlertCircle, TrendingUp, Calendar, FileText } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import Link from 'next/link'
import { motion } from 'framer-motion'
import type { ClinicalAnalytics } from '@/lib/types'

export default function PatientDashboard() {
  const { profile } = useAuth()
  const [analytics, setAnalytics] = useState<ClinicalAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [serviceOffline, setServiceOffline] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getClinicalAnalytics()
        setAnalytics(data)
      } catch {
        setServiceOffline(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return <div className="p-8 text-slate-400">Loading your health portal...</div>
  }

  const sortedTrends = [...(analytics?.trends || [])].sort(
    (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
  )

  const latestRisk = sortedTrends.length 
    ? sortedTrends[sortedTrends.length - 1].riskScore * 100
    : 0

  const chartData = sortedTrends.map((t) => ({
    date: new Date(t.createdAt).toLocaleDateString(),
    risk: Number((t.riskScore * 100).toFixed(1))
  }))

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4">
      <section className="medical-hero">
        <div className="hero-copy">
          <span className="live-badge"><i/> AI health monitoring</span>
          <h1>Welcome, {profile?.full_name || 'there'}</h1>
          <p>Your cardiovascular intelligence center. Review your latest signals, risk trend, and care recommendations in one place.</p>
          <div className="hero-actions">
            <Link href="/patient/assessment/new" className="hero-primary"><Activity size={18}/> Start assessment</Link>
            <Link href="/patient/reports" className="hero-secondary"><FileText size={18}/> View reports</Link>
          </div>
        </div>
        <motion.div className="character-stage" initial={{opacity:0,scale:.94,x:30}} animate={{opacity:1,scale:1,x:0}} transition={{duration:1,ease:[.22,1,.36,1]}}>
          <div className="character-aura"/>
          <motion.img src="/cardiovascular-character.png" alt="An original translucent anatomical figure highlighting the cardiovascular system" animate={{y:[0,-7,0]}} transition={{duration:5,repeat:Infinity,ease:'easeInOut'}}/>
          <motion.span className="heart-pulse" animate={{scale:[1,1.32,1],opacity:[.35,.8,.35]}} transition={{duration:1.05,repeat:Infinity,ease:'easeInOut'}}/>
        </motion.div>
      </section>

      {serviceOffline && <div className="service-notice" role="status"><AlertCircle size={18}/><div><strong>Live analytics are temporarily unavailable</strong><span>The dashboard remains available. Start the API service on port 8000 to restore your clinical data.</span></div></div>}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center shadow-lg">
          <div className="w-12 h-12 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center mr-4">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">Latest Risk Score</p>
            <h3 className="text-2xl font-bold text-slate-100">{latestRisk.toFixed(1)}%</h3>
          </div>
        </div>
        
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center shadow-lg">
          <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mr-4">
            <Heart className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">Risk Category</p>
            <h3 className="text-xl font-bold text-slate-100">
              {latestRisk > 50 ? 'High' : latestRisk > 20 ? 'Moderate' : 'Low'}
            </h3>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex items-center shadow-lg">
          <div className="w-12 h-12 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center mr-4">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-400">Assessments</p>
            <h3 className="text-2xl font-bold text-slate-100">{analytics?.trends?.length || 0}</h3>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Chart */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
          <h2 className="text-lg font-semibold text-slate-100 mb-6">Longitudinal Risk Trend</h2>
          {chartData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: 'none', borderRadius: '8px', color: '#fff' }}
                    labelFormatter={(label: string) => `Date: ${label}`}
                  />
                  <Line type="monotone" dataKey="risk" name="Risk Score" unit="%" stroke="#3b82f6" strokeWidth={3} dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center border-2 border-dashed border-slate-800 rounded-xl">
              <div className="text-center">
                <AlertCircle className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="text-slate-500">No predictions yet.</p>
              </div>
            </div>
          )}
        </div>

        {/* Quick Actions & Profile */}
        <div className="space-y-6">
          <div className="bg-gradient-to-br from-blue-900/50 to-slate-900 border border-blue-800/50 p-6 rounded-2xl shadow-lg">
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            <Link href="/patient/assessment/new" className="flex items-center w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl mb-3 transition-colors shadow-lg shadow-blue-900/20">
              <Activity className="w-5 h-5 mr-3" />
              <span className="font-medium">New Assessment</span>
            </Link>
            <Link href="/patient/reports" className="flex items-center w-full px-4 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl transition-colors">
              <FileText className="w-5 h-5 mr-3" />
              <span className="font-medium">View Reports</span>
            </Link>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-lg">
            <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center">
              <Calendar className="w-5 h-5 mr-2 text-slate-400" />
              Health Profile
            </h3>
            <ul className="space-y-3 text-sm">
              <li className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-500">Age</span>
                <span className="text-slate-200 font-medium">{profile?.age || 'N/A'}</span>
              </li>
              <li className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-500">BMI</span>
                <span className="text-slate-200 font-medium">{profile?.bmi || 'N/A'}</span>
              </li>
              <li className="flex justify-between border-b border-slate-800 pb-2">
                <span className="text-slate-500">Smoking</span>
                <span className="text-slate-200 font-medium">{profile?.smoking_status || 'N/A'}</span>
              </li>
            </ul>
          </div>

          <div className="bg-slate-900 border-2 border-emerald-900/50 p-6 rounded-2xl shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-emerald-600 text-[10px] font-bold px-2 py-1 uppercase tracking-wider text-white rounded-bl-lg">ABDM Sandbox Mode</div>
            <h3 className="text-lg font-semibold text-emerald-100 mb-2 flex items-center mt-2">
              <Activity className="w-5 h-5 mr-2 text-emerald-400" />
              National Health ID
            </h3>
            <p className="text-xs text-emerald-200/70 mb-4">
              Simulated integration with Ayushman Bharat Digital Mission (ABDM).
            </p>
            <div className="bg-slate-950 p-3 rounded-lg text-xs font-mono text-emerald-400 break-all border border-emerald-900">
              ABHA-ID: 14-{Math.floor(Math.random() * 9000 + 1000)}-{Math.floor(Math.random() * 9000 + 1000)}-{Math.floor(Math.random() * 9000 + 1000)}<br/>
              Status: Linked & Verified<br/>
              Consent: Active (Sandbox)
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
