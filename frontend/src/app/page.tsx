"use client"

import Link from 'next/link'
import { Activity, ShieldCheck, Stethoscope, ChevronRight } from 'lucide-react'
import { useAuth } from '@/components/auth/AuthProvider'
import { createClient } from '@/lib/supabase/client'

export default function LandingPage() {
  const { user, profile } = useAuth()
  const supabase = createClient()
  
  const handleLogout = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      if (signOut) {
        await signOut();
      }
      await supabase.auth.signOut();
    } catch (err) {
      console.error("Sign out error:", err);
    }
    window.location.href = '/login';
  }

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-200 flex flex-col font-sans selection:bg-blue-500/30 relative overflow-hidden">
      {/* Dynamic Mesh Background */}
      <div className="absolute inset-0 z-0 opacity-40 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/30 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-600/20 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />
        <div className="absolute top-[40%] left-[60%] w-[30%] h-[30%] bg-purple-600/20 rounded-full blur-[100px] pointer-events-none mix-blend-screen" />
      </div>
      {/* Header */}
      <header className="absolute top-0 w-full p-6 flex justify-between items-center z-50 border-b border-white/10 bg-[#0B0F19]/80 backdrop-blur-xl shadow-lg">
        <Link href="/" title="OmniFusion Landing Page" className="relative z-50 flex items-center space-x-3 cursor-pointer hover:opacity-90 transition-opacity">
          <Activity className="w-8 h-8 text-emerald-400" />
          <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
            Omni-Fusion
          </span>
        </Link>
        <div className="relative z-50 flex items-center space-x-4">
          {user ? (
            <>
              <button 
                type="button"
                onClick={handleLogout} 
                className="relative z-50 text-sm font-medium text-slate-300 hover:text-white transition-colors px-3.5 py-2 rounded-lg hover:bg-white/10 cursor-pointer"
              >
                Sign Out
              </button>
              <Link 
                href={profile?.role === 'DOCTOR' ? '/doctor' : '/patient'} 
                className="relative z-50 text-sm font-medium px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold rounded-full transition-all shadow-lg shadow-emerald-500/20 active:scale-95 cursor-pointer inline-block"
              >
                Go to Dashboard
              </Link>
            </>
          ) : (
            <>
              <Link href="/login" className="text-xs font-semibold px-3 py-1.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-full hover:bg-amber-500/20 transition-all">
                ✨ Demo Accounts
              </Link>
              <Link href="/login" className="text-sm font-medium text-slate-300 hover:text-white transition-colors">
                Log In
              </Link>
              <Link href="/signup" className="text-sm font-medium px-5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-full transition-all shadow-lg shadow-blue-900/20">
                Get Started
              </Link>
            </>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center pt-32 pb-20 px-4 relative z-10">

        <div className="max-w-4xl w-full text-center space-y-8 z-10 animate-in fade-in slide-in-from-bottom-8 duration-1000">
          <div className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-md text-sm font-semibold text-emerald-400 mb-6 shadow-xl shadow-black/20">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span>Platform Extension V2 Live</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white leading-[1.1] drop-shadow-2xl">
            The Future of <br className="hidden md:block" />
            <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-400 bg-clip-text text-transparent drop-shadow-lg">
              Cardiovascular Intelligence
            </span>
          </h1>
          
          <p className="text-lg md:text-xl text-slate-300 max-w-2xl mx-auto leading-relaxed font-medium drop-shadow-md">
            Omni-Fusion seamlessly integrates multimodal patient data—combining ECG waveforms, vitals, and longitudinal history—to deliver precise, AI-driven clinical insights.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8">
            {user ? (
              <Link href={profile?.role === 'DOCTOR' ? '/doctor' : '/patient'} className="group flex items-center justify-center w-full sm:w-auto px-8 py-4 bg-emerald-500 text-white font-semibold rounded-full hover:bg-emerald-400 transition-all hover:scale-105">
                Go to your Dashboard
                <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
            ) : (
              <>
                <Link href="/signup" className="group flex items-center justify-center w-full sm:w-auto px-8 py-4 bg-white text-slate-950 font-semibold rounded-full hover:bg-slate-100 transition-all duration-300 hover:scale-105 hover:shadow-[0_0_40px_rgba(255,255,255,0.3)] active:scale-95">
                  Get Started
                  <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link href="/login" className="flex items-center justify-center w-full sm:w-auto px-8 py-4 bg-white/5 border border-white/10 text-white font-semibold rounded-full backdrop-blur-md hover:bg-white/10 transition-all duration-300 hover:scale-105 hover:shadow-[0_0_40px_rgba(59,130,246,0.15)] active:scale-95 hover:border-white/20">
                  Sign In to Portal
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Feature Grid */}
        <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-3 gap-6 mt-32 z-10">
          <div className="bg-white/5 backdrop-blur-lg border border-white/10 p-8 rounded-3xl hover:bg-white/10 hover:border-blue-500/50 transition-all duration-300 shadow-2xl hover:-translate-y-1">
            <div className="w-12 h-12 bg-blue-500/20 text-blue-400 flex items-center justify-center rounded-2xl mb-6">
              <Activity className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Multimodal AI</h3>
            <p className="text-slate-400 leading-relaxed text-sm">
              Process ECG, vitals, and electronic health records simultaneously for a comprehensive cardiovascular risk profile.
            </p>
          </div>

          <div className="bg-white/5 backdrop-blur-lg border border-white/10 p-8 rounded-3xl hover:bg-white/10 hover:border-emerald-500/50 transition-all duration-300 shadow-2xl hover:-translate-y-1">
            <div className="w-12 h-12 bg-emerald-500/20 text-emerald-400 flex items-center justify-center rounded-2xl mb-6">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Enterprise Security</h3>
            <p className="text-slate-400 leading-relaxed text-sm">
              Role-based access control with secure JWT authentication and strict Row Level Security policies for medical data.
            </p>
          </div>

          <div className="bg-white/5 backdrop-blur-lg border border-white/10 p-8 rounded-3xl hover:bg-white/10 hover:border-teal-500/50 transition-all duration-300 shadow-2xl hover:-translate-y-1">
            <div className="w-12 h-12 bg-teal-500/20 text-teal-400 flex items-center justify-center rounded-2xl mb-6">
              <Stethoscope className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-white mb-3">Clinical Workflow</h3>
            <p className="text-slate-400 leading-relaxed text-sm">
              Seamlessly link patients with their respective doctors for collaborative review and automated AI report generation.
            </p>
          </div>
        </div>
      </main>

      <footer className="py-8 text-center text-slate-400 text-sm border-t border-white/10 z-10 bg-[#0B0F19]/50 backdrop-blur-md">
        &copy; {new Date().getFullYear()} Omni-Fusion Healthcare. AI-assisted diagnostics platform.
      </footer>
    </div>
  )
}
