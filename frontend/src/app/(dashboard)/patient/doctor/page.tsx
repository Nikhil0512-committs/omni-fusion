"use client"

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/auth/AuthProvider'
import { Users, Mail, Phone, MapPin, Loader2, Link2, KeyRound, Pill } from 'lucide-react'
import { api } from '@/lib/api'
import type { DoctorProfile } from '@/lib/types'
import { ChatBox } from '@/components/ChatBox'

export default function MyDoctorPage() {
  const { profile } = useAuth()
  const [doctor, setDoctor] = useState<DoctorProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [errorStr, setErrorStr] = useState<string | null>(null)
  const [availableDoctors, setAvailableDoctors] = useState<DoctorProfile[] | null>(null)
  const [searching, setSearching] = useState(false)
  const [requestingId, setRequestingId] = useState<string | null>(null)
  const [requestSent, setRequestSent] = useState<string | null>(null)
  const [doctorCode, setDoctorCode] = useState('')
  const [connectingCode, setConnectingCode] = useState(false)
  const supabase = createClient()

  useEffect(() => {
    async function fetchDoctor() {
      if (!profile) return

      try {
        // Fetch doctor_patient_links where patient_id matches
        const { data: link, error: linkError } = await supabase
          .from('doctor_patient_links')
          .select('doctor_id')
          .eq('patient_id', profile.id)
          .eq('status', 'accepted')
          .order('created_at', { ascending: true })
          .limit(1)
          .maybeSingle()

        if (linkError && linkError.code !== 'PGRST116') {
          throw linkError
        }

        if (link?.doctor_id) {
          const { data: docProfile, error: docError } = await supabase
            .from('profiles')
            .select('*')
            .eq('id', link.doctor_id)
            .single()
            
          if (docError) throw docError
          setDoctor({ id:docProfile.id, role:'DOCTOR', fullName:docProfile.full_name, email:docProfile.email, specialization:docProfile.specialization, hospital:docProfile.hospital, phone:docProfile.phone })
        }
      } catch (err: unknown) {
        console.error("Error fetching doctor:", err)
        setErrorStr(err instanceof Error ? err.message : "Failed to load doctor information.")
      } finally {
        setLoading(false)
      }
    }

    fetchDoctor()
  }, [profile, supabase])

  const findCardiologists = async () => {
    setSearching(true)
    setErrorStr(null)
    try {
      const { data, error } = await supabase
        .from('profiles')
        .select('id, full_name, email, specialization, hospital, phone')
        .eq('role', 'DOCTOR')
        .order('full_name')
      if (error) throw error
      setAvailableDoctors((data || []).map(item => ({ id:item.id,role:'DOCTOR' as const,fullName:item.full_name,email:item.email,specialization:item.specialization,hospital:item.hospital,phone:item.phone })))
    } catch {
      setAvailableDoctors(null)
      setErrorStr('Cardiologists could not be loaded right now. Please try again.')
    } finally {
      setSearching(false)
    }
  }

  const requestDoctor = async (doctorId: string) => {
    setRequestingId(doctorId)
    setErrorStr(null)
    try {
      await api.requestLink(doctorId)
      setRequestSent(doctorId)
    } catch (error) {
      setErrorStr(error instanceof Error ? error.message : 'Could not send the connection request.')
    } finally {
      setRequestingId(null)
    }
  }

  const connectWithCode = async () => {
    if (!doctorCode.trim()) return
    setConnectingCode(true)
    setErrorStr(null)
    try {
      const result = await api.connectByDoctorCode(doctorCode)
      setDoctor(result.doctor)
      setAvailableDoctors(null)
    } catch (error) {
      setErrorStr(error instanceof Error ? error.message : 'The doctor code is invalid.')
    } finally {
      setConnectingCode(false)
    }
  }

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
      </div>
    )
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">My Clinical Team</h1>
        <p className="text-slate-400">View information about your assigned cardiologist and care team.</p>
      </div>

      {errorStr && (
        <div className="mb-6 bg-red-500/10 border border-red-500/50 text-red-400 p-4 rounded-xl">
          {errorStr}
        </div>
      )}

      {doctor ? (
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 relative overflow-hidden">
          {/* Decorative background */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3" />
          
          <div className="relative z-10 flex flex-col md:flex-row gap-8 items-start">
            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-emerald-400 to-blue-500 p-1 shrink-0">
              <div className="w-full h-full bg-slate-900 rounded-xl flex items-center justify-center">
                <Users className="w-10 h-10 text-emerald-400" />
              </div>
            </div>
            
            <div className="flex-1 space-y-4">
              <div>
                <div className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 mb-2 border border-emerald-500/20">
                  Primary Cardiologist
                </div>
                <h2 className="text-2xl font-bold text-white">
                  {doctor.fullName?.startsWith('Dr') ? doctor.fullName : `Dr. ${doctor.fullName}`}
                </h2>
                {doctor.specialization && (
                  <p className="text-slate-400">{doctor.specialization}</p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-800">
                <div className="flex items-center text-slate-300">
                  <Mail className="w-5 h-5 text-slate-500 mr-3" />
                  <a href={`mailto:${doctor.email}`} className="hover:text-emerald-400 transition-colors">
                    {doctor.email}
                  </a>
                </div>
                {doctor.phone && (
                  <div className="flex items-center text-slate-300">
                    <Phone className="w-5 h-5 text-slate-500 mr-3" />
                    {doctor.phone}
                  </div>
                )}
                {doctor.hospital && (
                  <div className="flex items-center text-slate-300 sm:col-span-2">
                    <MapPin className="w-5 h-5 text-slate-500 mr-3 shrink-0" />
                    <span>{doctor.hospital}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="mt-8 relative z-10 border-t border-slate-800 pt-8">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <Pill className="w-5 h-5 mr-2 text-indigo-400" />
              Active Prescriptions
            </h3>
            {(!profile?.medications || profile.medications.length === 0) ? (
              <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 text-center text-slate-500 mb-8">
                No active prescriptions from your doctor.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
                {profile.medications.map((med: any, idx: number) => (
                  <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-5 shadow-sm">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-white font-medium text-lg">{med.medicationName}</h4>
                      {med.createdAt && <span className="text-xs text-slate-500">{new Date(med.createdAt).toLocaleDateString()}</span>}
                    </div>
                    <div className="grid grid-cols-2 gap-y-2 text-sm mt-3">
                      <div><span className="text-slate-500 block text-[11px] uppercase tracking-wider mb-1">Dosage</span><span className="text-slate-300 font-medium">{med.dosage}</span></div>
                      <div><span className="text-slate-500 block text-[11px] uppercase tracking-wider mb-1">Frequency</span><span className="text-slate-300 font-medium">{med.frequency}</span></div>
                      <div><span className="text-slate-500 block text-[11px] uppercase tracking-wider mb-1">Duration</span><span className="text-slate-300 font-medium">{med.duration}</span></div>
                    </div>
                    {med.notes && <p className="mt-4 text-xs text-slate-400 bg-slate-900 border border-slate-800 p-3 rounded-lg leading-relaxed">{med.notes}</p>}
                  </div>
                ))}
              </div>
            )}

            <div className="border-t border-slate-800 pt-8 mt-8">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center">
                <Users className="w-5 h-5 mr-2 text-emerald-400" />
                Direct Message
              </h3>
              <ChatBox otherUserId={doctor.id} otherUserName={doctor.fullName?.startsWith('Dr') ? doctor.fullName : `Dr. ${doctor.fullName}`} />
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-12 text-center flex flex-col items-center">
          <div className="w-20 h-20 bg-slate-800/50 rounded-full flex items-center justify-center mb-6">
            <Link2 className="w-10 h-10 text-slate-500" />
          </div>
          <h3 className="text-xl font-medium text-white mb-3">No Doctor Assigned</h3>
          <p className="text-slate-400 max-w-md mb-8">
            Enter the connection code shared by your doctor, or browse available cardiologists.
          </p>
          <div className="w-full max-w-md mb-5">
            <label className="text-sm font-semibold text-slate-300 mb-2 flex items-center justify-center gap-2"><KeyRound className="w-4 h-4" /> Doctor Connection Code</label>
            <div className="flex gap-2">
              <input value={doctorCode} onChange={(event) => setDoctorCode(event.target.value.toUpperCase())} placeholder="OF-1234ABCD" className="flex-1 bg-white border border-slate-800 rounded-xl px-4 py-3 text-center font-mono uppercase" />
              <button onClick={connectWithCode} disabled={connectingCode || !doctorCode.trim()} className="px-5 py-3 bg-emerald-600 text-white rounded-xl font-semibold disabled:opacity-50">{connectingCode ? 'Connecting...' : 'Connect'}</button>
            </div>
          </div>
          <button onClick={findCardiologists} disabled={searching} className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl transition-colors font-medium shadow-lg shadow-emerald-900/20 disabled:opacity-60 flex items-center gap-2">
            {searching && <Loader2 className="w-4 h-4 animate-spin" />}
            {searching ? 'Finding Cardiologists...' : 'Find a Cardiologist'}
          </button>

          {availableDoctors?.length === 0 && !searching && (
            <div className="mt-7 px-5 py-4 rounded-2xl bg-slate-800/50 border border-slate-800 w-full max-w-md" role="status">
              <p className="font-semibold text-slate-300">No doctors available</p>
              <p className="text-sm text-slate-500 mt-1">There are currently no registered cardiologists accepting connections.</p>
            </div>
          )}

          {availableDoctors && availableDoctors.length > 0 && (
            <div className="mt-8 w-full text-left grid gap-3">
              {availableDoctors.map((item) => (
                <div key={item.id} className="bg-white border border-slate-800 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className="w-11 h-11 rounded-xl bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0"><Users className="w-5 h-5" /></div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-slate-200">
                      {(item.fullName || '').startsWith('Dr') ? item.fullName : `Dr. ${item.fullName || 'Cardiologist'}`}
                    </h4>
                    <p className="text-sm text-slate-500">{item.specialization || 'Cardiology'}{item.hospital ? ` · ${item.hospital}` : ''}</p>
                  </div>
                  <button onClick={() => requestDoctor(item.id)} disabled={requestingId === item.id || requestSent === item.id} className="px-4 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-semibold disabled:opacity-60">
                    {requestingId === item.id ? 'Sending...' : requestSent === item.id ? 'Request Sent' : 'Request Connection'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
