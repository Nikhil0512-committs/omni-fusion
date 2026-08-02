"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import Link from 'next/link'
import { ArrowLeft, UserCheck, Stethoscope, Sparkles, HeartPulse, ShieldCheck, Lock, Mail } from 'lucide-react'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  const handleLoginWithCredentials = async (loginEmail: string, loginPass: string) => {
    setLoading(true)
    setError(null)

    const { error } = await supabase.auth.signInWithPassword({
      email: loginEmail,
      password: loginPass,
    })

    if (error) {
      setError(error.message)
      setLoading(false)
    } else {
      const { data: userAuth } = await supabase.auth.getUser()
      if (userAuth.user) {
        const { data: profileData } = await supabase
          .from('profiles')
          .select('role')
          .eq('id', userAuth.user.id)
          .single()
        
        if (profileData?.role === 'DOCTOR') {
          router.push('/doctor')
        } else if (profileData?.role === 'PATIENT') {
          router.push('/patient')
        } else {
          const intendedRole = localStorage.getItem('intended_role')
          if (intendedRole === 'DOCTOR') {
            router.push('/onboarding/doctor')
          } else {
            router.push('/onboarding/patient')
          }
        }
      } else {
        router.push('/')
      }
      router.refresh()
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    await handleLoginWithCredentials(email, password)
  }

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center p-4 md:p-8" style={{ background: 'radial-gradient(circle at 50% 0%, #0f2b38 0%, #08131a 100%)' }}>
      {/* Top Header Navigation */}
      <div className="w-full max-w-6xl mb-8 flex items-center justify-between border-b border-slate-800/80 pb-4">
        <Link href="/" className="inline-flex items-center gap-2 text-slate-300 hover:text-white transition-colors text-sm font-semibold">
          <ArrowLeft className="w-4 h-4 text-teal-400" /> Back to Landing Page
        </Link>
        <Link href="/" className="flex items-center gap-2 text-xl font-extrabold text-white decoration-none">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-400 to-cyan-600 flex items-center justify-center text-slate-950">
            <HeartPulse className="w-5 h-5" />
          </div>
          <span>Omni<span className="text-teal-400">Fusion</span></span>
        </Link>
      </div>

      <div className="w-full max-w-6xl flex flex-col lg:flex-row items-stretch justify-center gap-8 my-auto">
        {/* Main Sign In Form */}
        <div className="w-full lg:w-96 bg-white rounded-2xl shadow-2xl p-6 md:p-8 shrink-0 flex flex-col justify-between border border-slate-200">
          <div>
            <div className="text-center mb-6">
              <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center mx-auto mb-3">
                <ShieldCheck className="w-6 h-6 text-teal-600" />
              </div>
              <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                Welcome Back
              </h1>
              <p className="text-slate-500 text-xs mt-1">Sign in to access your medical portal</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded-xl text-xs font-medium">
                  {error}
                </div>
              )}
              
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">Email Address</label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="doctor@example.com"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition-all font-medium"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-2.5 text-sm text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white transition-all font-medium"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 text-white font-bold py-3 px-4 rounded-xl transition-all shadow-lg shadow-teal-600/25 disabled:opacity-50 mt-2 text-sm cursor-pointer"
              >
                {loading ? 'Signing in...' : 'Sign In to Portal'}
              </button>
            </form>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 text-center text-xs text-slate-500 font-medium">
            Don't have an account?{' '}
            <Link href="/signup" className="text-teal-600 hover:text-teal-700 font-bold underline">
              Create Account
            </Link>
          </div>
        </div>

        {/* Demo Accounts Panel */}
        <div className="w-full flex-1 bg-white rounded-2xl shadow-2xl p-6 md:p-8 border border-slate-200 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-4 mb-6 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <h2 className="text-lg font-extrabold text-slate-900">Instant Demo Accounts</h2>
                  <p className="text-xs text-slate-500">Select any role below to evaluate the live dashboard</p>
                </div>
              </div>
              <span className="text-xs bg-amber-100 text-amber-800 border border-amber-200 px-3 py-1 rounded-full font-bold">
                ⚡ 1-Click Quick Login
              </span>
            </div>

            <div className="space-y-6">
              {/* Doctor Accounts */}
              <div>
                <div className="flex items-center gap-2 text-xs font-extrabold text-teal-700 uppercase tracking-wider mb-3">
                  <Stethoscope className="w-4 h-4 text-teal-600" /> Demo Doctor Accounts
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { name: 'Dr. Ananya Sharma', role: 'Cardiology', email: 'demo.doctor1@omnifusion.demo' },
                    { name: 'Dr. Rajiv Menon', role: 'Internal Medicine', email: 'demo.doctor2@omnifusion.demo' },
                    { name: 'Dr. Priya Nair', role: 'Cardiology Fellow', email: 'demo.doctor3@omnifusion.demo' }
                  ].map((doc) => (
                    <div
                      key={doc.email}
                      className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/80 hover:bg-teal-50/50 hover:border-teal-300 transition-all flex flex-col justify-between group"
                    >
                      <div>
                        <div className="font-bold text-sm text-slate-900 group-hover:text-teal-800">{doc.name}</div>
                        <div className="text-xs font-semibold text-teal-600 mt-0.5">{doc.role}</div>
                      </div>
                      <button
                        type="button"
                        disabled={loading}
                        onClick={() => {
                          setEmail(doc.email)
                          setPassword('DemoPassword123!')
                          handleLoginWithCredentials(doc.email, 'DemoPassword123!')
                        }}
                        className="mt-3 w-full py-2 px-3 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold transition-all shadow-sm shadow-teal-600/20 cursor-pointer"
                      >
                        Login as Doctor →
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Patient Accounts */}
              <div>
                <div className="flex items-center gap-2 text-xs font-extrabold text-cyan-700 uppercase tracking-wider mb-3">
                  <UserCheck className="w-4 h-4 text-cyan-600" /> Demo Patient Accounts
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { name: 'Ramesh Iyer', risk: 'Critical Risk', email: 'demo.patient1@omnifusion.demo', badgeBg: '#fef2f2', badgeText: '#dc2626', badgeBorder: '#fecaca' },
                    { name: 'Sunita Verma', risk: 'Moderate Risk', email: 'demo.patient2@omnifusion.demo', badgeBg: '#fffbe6', badgeText: '#d97706', badgeBorder: '#fef08a' },
                    { name: 'Arjun Kapoor', risk: 'Low Risk', email: 'demo.patient3@omnifusion.demo', badgeBg: '#ecfdf5', badgeText: '#059669', badgeBorder: '#a7f3d0' },
                    { name: 'Meera Joshi', risk: 'High Risk', email: 'demo.patient4@omnifusion.demo', badgeBg: '#fff7ed', badgeText: '#ea580c', badgeBorder: '#ffedd5' },
                    { name: 'Vikram Singh', risk: 'Moderate Risk', email: 'demo.patient5@omnifusion.demo', badgeBg: '#fffbe6', badgeText: '#d97706', badgeBorder: '#fef08a' }
                  ].map((pat) => (
                    <div
                      key={pat.email}
                      className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/80 hover:bg-cyan-50/50 hover:border-cyan-300 transition-all flex flex-col justify-between group"
                    >
                      <div>
                        <div className="font-bold text-sm text-slate-900 group-hover:text-cyan-800">{pat.name}</div>
                        <span 
                          className="inline-block mt-1 text-[10px] font-extrabold px-2 py-0.5 rounded-full border"
                          style={{ backgroundColor: pat.badgeBg, color: pat.badgeText, borderColor: pat.badgeBorder }}
                        >
                          {pat.risk}
                        </span>
                      </div>
                      <button
                        type="button"
                        disabled={loading}
                        onClick={() => {
                          setEmail(pat.email)
                          setPassword('DemoPassword123!')
                          handleLoginWithCredentials(pat.email, 'DemoPassword123!')
                        }}
                        className="mt-3 w-full py-2 px-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-xs font-bold transition-all shadow-sm shadow-cyan-600/20 cursor-pointer"
                      >
                        Login as Patient →
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>🔒 Secure OAuth 2.0 & Encrypted Authentication</span>
            <span className="font-semibold text-teal-700">MIMIC-IV Benchmarked</span>
          </div>
        </div>
      </div>
    </div>
  )
}

