"use client"

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'

export default function DoctorOnboarding() {
  const router = useRouter()
  const { profile } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    role: 'DOCTOR',
    full_name: '',
    specialization: 'Cardiology',
    hospital: '',
    medical_registration_number: '',
    phone: '',
    bio: '',
  })

  // If already onboarded, redirect
  if (profile) {
    router.push(`/dashboard/${profile.role.toLowerCase()}`)
    return null
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await api.onboardProfile({ role: 'DOCTOR', fullName: formData.full_name, specialization: formData.specialization, hospital: formData.hospital, medicalRegistrationNumber: formData.medical_registration_number, phone: formData.phone, bio: formData.bio })
      window.location.href = '/doctor'
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Unable to create doctor profile')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex flex-col items-center justify-center p-4 md:p-8">
      {/* Top Header Navigation */}
      <div className="w-full max-w-xl mb-6 flex items-center justify-between border-b border-slate-800 pb-4">
        <Link href="/" className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition-colors text-sm font-medium">
          <ArrowLeft className="w-4 h-4" /> Back to Landing Page
        </Link>
        <Link href="/" className="text-xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          Omni-Fusion
        </Link>
      </div>
      <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl">
        <h1 className="text-2xl font-bold mb-2">Doctor Verification</h1>
        <p className="text-slate-400 mb-8 text-sm">Please provide your professional credentials.</p>
        
        {error && (
          <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm mb-1 text-slate-300">Full Name (with title)</label>
            <input name="full_name" placeholder="Dr. John Doe" value={formData.full_name} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 focus:border-emerald-500 focus:outline-none" required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm mb-1 text-slate-300">Specialization</label>
              <select name="specialization" value={formData.specialization} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 focus:border-emerald-500 focus:outline-none">
                <option>Cardiology</option>
                <option>General Practice</option>
                <option>Internal Medicine</option>
                <option>Other</option>
              </select>
            </div>
            <div>
              <label className="block text-sm mb-1 text-slate-300">Registration Number</label>
              <input name="medical_registration_number" placeholder="XYZ-12345" value={formData.medical_registration_number} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 focus:border-emerald-500 focus:outline-none" required />
            </div>
          </div>
          <div>
            <label className="block text-sm mb-1 text-slate-300">Hospital / Clinic</label>
            <input name="hospital" value={formData.hospital} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 focus:border-emerald-500 focus:outline-none" required />
          </div>
          <div>
            <label className="block text-sm mb-1 text-slate-300">Contact Phone</label>
            <input name="phone" value={formData.phone} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 focus:border-emerald-500 focus:outline-none" required />
          </div>
          <div>
            <label className="block text-sm mb-1 text-slate-300">Bio (Optional)</label>
            <textarea name="bio" value={formData.bio} onChange={handleChange} className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 focus:border-emerald-500 focus:outline-none h-24" placeholder="Brief professional background..." />
          </div>

          <button type="submit" disabled={loading} className="w-full mt-6 px-4 py-3 bg-emerald-600 rounded-lg hover:bg-emerald-500 font-medium transition-colors disabled:opacity-50 text-white">
            {loading ? 'Submitting...' : 'Complete Verification'}
          </button>
        </form>
      </div>
    </div>
  )
}
