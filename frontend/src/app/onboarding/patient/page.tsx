"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import { useAuth } from '@/components/auth/AuthProvider'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export default function PatientOnboarding() {
  const router = useRouter()
  const { user, profile } = useAuth()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    role: 'PATIENT',
    full_name: '',
    date_of_birth: '',
    sex: 'M',
    height_cm: '',
    weight_kg: '',
    smoking_status: 'Never',
    alcohol_use: 'Never',
    exercise_frequency: 'Rarely',
    consent: false,
  })

  // If already onboarded, redirect
  if (profile) {
    router.push(`/dashboard/${profile.role.toLowerCase()}`)
    return null
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const val = type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    setFormData(prev => ({ ...prev, [name]: val }))
  }

  const handleSubmit = async () => {
    if (!formData.consent) {
      setError("You must provide consent to continue.")
      return
    }
    
    setLoading(true)
    setError(null)
    try {
      await api.onboardProfile({
        role: 'PATIENT',
        fullName: formData.full_name,
        dateOfBirth: formData.date_of_birth || null,
        sex: formData.sex,
        heightCm: formData.height_cm ? parseFloat(formData.height_cm) : null,
        weightKg: formData.weight_kg ? parseFloat(formData.weight_kg) : null,
        smokingStatus: formData.smoking_status,
        alcoholUse: formData.alcohol_use,
        exerciseFrequency: formData.exercise_frequency,
      })
      // Refresh page to trigger RoleGuard or fetch new profile
      window.location.href = '/patient'
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unable to create patient profile')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col items-center justify-center p-4 md:p-8">
      {/* Top Header Navigation */}
      <div className="w-full max-w-2xl mb-6 flex items-center justify-between border-b border-slate-800 pb-4">
        <Link href="/" className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Landing Page
        </Link>
        <Link href="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Omni-Fusion
        </Link>
      </div>
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl p-8">
        <h1 className="text-2xl font-bold mb-6">Patient Onboarding</h1>
        
        {/* Progress Bar */}
        <div className="flex gap-2 mb-8">
          {[1, 2, 3, 4].map(s => (
            <div key={s} className={`h-2 flex-1 rounded-full ${step >= s ? 'bg-blue-500' : 'bg-slate-800'}`} />
          ))}
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
            <h2 className="text-xl font-semibold mb-4">Personal Identity</h2>
            <div>
              <label className="block text-sm mb-1">Full Name</label>
              <input name="full_name" value={formData.full_name} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded p-2" required />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm mb-1">Date of Birth</label>
                <input type="date" name="date_of_birth" value={formData.date_of_birth} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded p-2" />
              </div>
              <div>
                <label className="block text-sm mb-1">Sex at Birth</label>
                <select name="sex" value={formData.sex} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded p-2">
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="O">Other</option>
                </select>
              </div>
            </div>
            <button onClick={() => setStep(2)} className="mt-6 px-4 py-2 bg-blue-600 rounded hover:bg-blue-500 transition-colors float-right">Next</button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
            <h2 className="text-xl font-semibold mb-4">Physical Attributes</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm mb-1">Height (cm)</label>
                <input type="number" name="height_cm" value={formData.height_cm} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded p-2" />
              </div>
              <div>
                <label className="block text-sm mb-1">Weight (kg)</label>
                <input type="number" name="weight_kg" value={formData.weight_kg} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded p-2" />
              </div>
            </div>
            <div className="flex justify-between mt-6">
              <button onClick={() => setStep(1)} className="px-4 py-2 bg-slate-800 rounded hover:bg-slate-700 transition-colors">Back</button>
              <button onClick={() => setStep(3)} className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-500 transition-colors">Next</button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
            <h2 className="text-xl font-semibold mb-4">Lifestyle</h2>
            <div>
              <label className="block text-sm mb-1">Smoking Status</label>
              <select name="smoking_status" value={formData.smoking_status} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded p-2">
                <option>Never</option>
                <option>Former</option>
                <option>Current</option>
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1">Alcohol Use</label>
              <select name="alcohol_use" value={formData.alcohol_use} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded p-2">
                <option>Never</option>
                <option>Occasionally</option>
                <option>Frequently</option>
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1">Exercise Frequency</label>
              <select name="exercise_frequency" value={formData.exercise_frequency} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded p-2">
                <option>Rarely</option>
                <option>1-3 times/week</option>
                <option>4+ times/week</option>
              </select>
            </div>
            <div className="flex justify-between mt-6">
              <button onClick={() => setStep(2)} className="px-4 py-2 bg-slate-800 rounded hover:bg-slate-700 transition-colors">Back</button>
              <button onClick={() => setStep(4)} className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-500 transition-colors">Next</button>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
            <h2 className="text-xl font-semibold mb-4">Privacy & Consent</h2>
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-sm space-y-2 text-slate-400">
              <p><strong>What is collected:</strong> We collect your identity, physical, lifestyle, and medical prediction data to form a longitudinal health record.</p>
              <p><strong>AI Limitations:</strong> Predictions are generated by AI models and are NOT definitive medical diagnoses. Always consult a real doctor.</p>
              <p><strong>Collaboration:</strong> You may share these predictions with your doctor via the platform.</p>
            </div>
            
            <label className="flex items-start gap-3 mt-4 cursor-pointer">
              <input type="checkbox" name="consent" checked={formData.consent} onChange={handleChange} className="mt-1" />
              <span className="text-sm">I explicitly consent to the collection and processing of my health data and acknowledge the AI limitations.</span>
            </label>

            <div className="flex justify-between mt-6">
              <button onClick={() => setStep(3)} className="px-4 py-2 bg-slate-800 rounded hover:bg-slate-700 transition-colors">Back</button>
              <button onClick={handleSubmit} disabled={loading} className="px-4 py-2 bg-emerald-600 rounded hover:bg-emerald-500 transition-colors">
                {loading ? 'Submitting...' : 'Complete Onboarding'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
