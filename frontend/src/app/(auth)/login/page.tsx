"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import Link from 'next/link'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
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

  return (
    <div className="min-h-screen flex flex-col md:flex-row items-center justify-center bg-slate-950 text-slate-100 p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Omni-Fusion
          </h1>
          <p className="text-slate-400 mt-2">Sign in to your account</p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg text-sm">
              {error}
            </div>
          )}
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-blue-500 transition-colors"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-slate-100 focus:outline-none focus:border-blue-500 transition-colors"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors disabled:opacity-50 mt-4"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-400">
          Don't have an account?{' '}
          <Link href="/signup" className="text-blue-400 hover:text-blue-300">
            Sign up
          </Link>
        </div>
      </div>

      {process.env.NEXT_PUBLIC_DEMO_MODE === 'true' && (
        <div className="w-full max-w-4xl mt-8 md:mt-0 md:ml-8">
          <div className="bg-white border border-slate-200 rounded-2xl shadow-xl p-8">
            <h2 className="text-xl font-semibold mb-6 text-slate-900">Demo Accounts</h2>
            
            <div className="mb-6">
              <h3 className="text-sm font-medium text-slate-500 mb-3">Doctors</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {[
                  { name: 'Dr. Ananya Sharma', role: 'Cardiology', email: 'demo.doctor1@omnifusion.demo' },
                  { name: 'Dr. Rajiv Menon', role: 'Internal Medicine', email: 'demo.doctor2@omnifusion.demo' },
                  { name: 'Dr. Priya Nair', role: 'Cardiology (Fellow)', email: 'demo.doctor3@omnifusion.demo' }
                ].map((doc) => (
                  <button
                    key={doc.email}
                    onClick={() => { setEmail(doc.email); setPassword('DemoPassword123!'); }}
                    className="flex flex-col text-left p-4 rounded-xl border border-slate-200 bg-slate-50 hover:border-blue-500/50 hover:bg-blue-50 transition-colors"
                  >
                    <span className="font-medium text-slate-900">{doc.name}</span>
                    <span className="text-xs text-slate-500 mt-1">{doc.role}</span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-slate-500 mb-3">Patients</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                {[
                  { name: 'Ramesh Iyer', risk: 'Critical Risk', email: 'demo.patient1@omnifusion.demo', color: 'text-red-400' },
                  { name: 'Sunita Verma', risk: 'Moderate Risk', email: 'demo.patient2@omnifusion.demo', color: 'text-yellow-400' },
                  { name: 'Arjun Kapoor', risk: 'Low Risk', email: 'demo.patient3@omnifusion.demo', color: 'text-green-400' },
                  { name: 'Meera Joshi', risk: 'High Risk (Flagged)', email: 'demo.patient4@omnifusion.demo', color: 'text-orange-400' },
                  { name: 'Vikram Singh', risk: 'Moderate Risk', email: 'demo.patient5@omnifusion.demo', color: 'text-yellow-400' }
                ].map((pat) => (
                  <button
                    key={pat.email}
                    onClick={() => { setEmail(pat.email); setPassword('DemoPassword123!'); }}
                    className="flex flex-col text-left p-4 rounded-xl border border-slate-200 bg-slate-50 hover:border-blue-500/50 hover:bg-blue-50 transition-colors"
                  >
                    <span className="font-medium text-slate-900">{pat.name}</span>
                    <span className={`text-xs mt-1 font-medium ${pat.color.replace('400', '600')}`}>{pat.risk}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
