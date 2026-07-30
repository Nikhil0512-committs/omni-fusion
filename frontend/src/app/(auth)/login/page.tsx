"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import Link from 'next/link'
import { ArrowLeft, UserCheck, Stethoscope, Sparkles } from 'lucide-react'

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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center p-4 md:p-8">
      {/* Top Header Navigation */}
      <div className="w-full max-w-6xl mb-6 flex items-center justify-between border-b border-slate-800 pb-4">
        <Link href="/" className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Landing Page
        </Link>
        <Link href="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Omni-Fusion
        </Link>
      </div>

      <div className="w-full max-w-6xl flex flex-col lg:flex-row items-start justify-center gap-8 my-auto">
        {/* Main Sign In Form */}
        <div className="w-full lg:w-96 bg-slate-900 border border-slate-800 rounded-2xl shadow-xl p-6 md:p-8 shrink-0">
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
              Welcome Back
            </h1>
            <p className="text-slate-400 text-sm mt-1">Sign in to access your portal</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg text-sm">
                {error}
              </div>
            )}
            
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="doctor@example.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500 transition-colors"
                required
              />
            </div>
            
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-blue-500 transition-colors"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-600 to-emerald-600 hover:from-blue-500 hover:to-emerald-500 text-white font-medium py-2.5 px-4 rounded-lg transition-all shadow-md disabled:opacity-50 mt-2 text-sm"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-800 text-center text-xs text-slate-400">
            Don't have an account?{' '}
            <Link href="/signup" className="text-blue-400 hover:text-blue-300 font-medium">
              Create Account
            </Link>
          </div>
        </div>

        {/* Demo Accounts Panel */}
        <div className="w-full flex-1 bg-slate-900/90 border border-slate-800 rounded-2xl shadow-xl p-6 md:p-8">
          <div className="flex items-center gap-2 mb-6">
            <Sparkles className="w-5 h-5 text-amber-400" />
            <h2 className="text-lg font-semibold text-slate-100">Instant Demo Accounts</h2>
            <span className="ml-auto text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2.5 py-0.5 rounded-full font-medium">
              1-Click Demo Login
            </span>
          </div>

          <div className="space-y-6">
            {/* Doctors */}
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                <Stethoscope className="w-4 h-4 text-emerald-400" /> Demo Doctor Accounts
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { name: 'Dr. Ananya Sharma', role: 'Cardiology', email: 'demo.doctor1@omnifusion.demo' },
                  { name: 'Dr. Rajiv Menon', role: 'Internal Medicine', email: 'demo.doctor2@omnifusion.demo' },
                  { name: 'Dr. Priya Nair', role: 'Fellow', email: 'demo.doctor3@omnifusion.demo' }
                ].map((doc) => (
                  <div
                    key={doc.email}
                    className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-emerald-500/50 hover:bg-slate-950 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="font-medium text-sm text-slate-200">{doc.name}</div>
                      <div className="text-xs text-slate-400">{doc.role}</div>
                    </div>
                    <button
                      type="button"
                      disabled={loading}
                      onClick={() => {
                        setEmail(doc.email)
                        setPassword('DemoPassword123!')
                        handleLoginWithCredentials(doc.email, 'DemoPassword123!')
                      }}
                      className="mt-3 w-full py-1.5 px-3 bg-emerald-600/20 hover:bg-emerald-600 text-emerald-300 hover:text-white border border-emerald-500/30 rounded-lg text-xs font-medium transition-all"
                    >
                      Login as Doctor
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Patients */}
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                <UserCheck className="w-4 h-4 text-blue-400" /> Demo Patient Accounts
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { name: 'Ramesh Iyer', risk: 'Critical Risk', email: 'demo.patient1@omnifusion.demo', color: 'text-red-400 bg-red-500/10 border-red-500/20' },
                  { name: 'Sunita Verma', risk: 'Moderate Risk', email: 'demo.patient2@omnifusion.demo', color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
                  { name: 'Arjun Kapoor', risk: 'Low Risk', email: 'demo.patient3@omnifusion.demo', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
                  { name: 'Meera Joshi', risk: 'High Risk', email: 'demo.patient4@omnifusion.demo', color: 'text-orange-400 bg-orange-500/10 border-orange-500/20' },
                  { name: 'Vikram Singh', risk: 'Moderate Risk', email: 'demo.patient5@omnifusion.demo', color: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' }
                ].map((pat) => (
                  <div
                    key={pat.email}
                    className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 hover:border-blue-500/50 hover:bg-slate-950 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="font-medium text-sm text-slate-200">{pat.name}</div>
                      <span className={`inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded border ${pat.color}`}>
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
                      className="mt-3 w-full py-1.5 px-3 bg-blue-600/20 hover:bg-blue-600 text-blue-300 hover:text-white border border-blue-500/30 rounded-lg text-xs font-medium transition-all"
                    >
                      Login as Patient
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
