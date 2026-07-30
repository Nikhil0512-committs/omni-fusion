"use client"

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { useAuth } from '@/components/auth/AuthProvider'
import { Loader2, ArrowLeft, FileText, User, Calendar, Activity, Plus, MessageSquare } from 'lucide-react'
import Link from 'next/link'
import { api } from '@/lib/api'
import type { DoctorNote, Profile, StoredPrediction } from '@/lib/types'
import { TriageBadge } from '@/components/TriageBadge'
import { ClinicalSummaryCard } from '@/components/ClinicalSummaryCard'

import { HistoricalEcgViewer } from '@/components/HistoricalEcgViewer'
import { RiskForecastChart } from '@/components/RiskForecastChart'
import { ReportComparison } from '@/components/ReportComparison'
import { ChatBox } from '@/components/ChatBox'

export default function PatientDetailsPage() {
  const { id } = useParams()
  const patientId = id as string
  const { profile } = useAuth()
  const supabase = createClient()

  const [patient, setPatient] = useState<Profile | null>(null)
  const [predictions, setPredictions] = useState<StoredPrediction[]>([])
  const [loading, setLoading] = useState(true)
  
  const [noteText, setNoteText] = useState('')
  const [activePredictionId, setActivePredictionId] = useState<string | null>(null)
  const [savingNote, setSavingNote] = useState(false)
  
  const [showPrescriptionForm, setShowPrescriptionForm] = useState(false)
  const [rxForm, setRxForm] = useState({ medicationName: '', dosage: '', frequency: '', duration: '', notes: '' })
  const [savingRx, setSavingRx] = useState(false)

  useEffect(() => {
    async function loadData() {
      if (!profile || !patientId) return

      try {
        const record = await api.getPatientRecord(patientId)
        setPatient(record.profile)
        setPredictions(record.predictions || [])

      } catch (err) {
        console.error("Error loading patient details:", err)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [patientId, profile, supabase])

  const handleSaveNote = async () => {
    if (!activePredictionId || !noteText.trim()) return
    setSavingNote(true)

    try {
      await api.addDoctorNote(activePredictionId, noteText, 'normal')

      // Optimistically update UI
      setPredictions(prev => prev.map(p => {
        if (p.id === activePredictionId) {
          return {
            ...p,
            doctorNotes: [...p.doctorNotes, { id: `local-${Date.now()}`, note: noteText, createdAt: new Date().toISOString() }]
          }
        }
        return p
      }))
      
      setNoteText('')
      setActivePredictionId(null)
    } catch (err) {
      console.error("Error saving note:", err)
      alert("Failed to save note.")
    } finally {
      setSavingNote(false)
    }
  }

  const handleSavePrescription = async () => {
    if (!rxForm.medicationName || !rxForm.dosage || !rxForm.frequency || !rxForm.duration) {
      alert("Please fill all required prescription fields.")
      return
    }
    setSavingRx(true)
    try {
      await api.addPrescription(patientId, rxForm.medicationName, rxForm.dosage, rxForm.frequency, rxForm.duration, rxForm.notes)
      // Optimistically update UI
      setPatient(prev => prev ? {
        ...prev,
        medications: [...(prev.medications || []), { id: `local-${Date.now()}`, ...rxForm, createdAt: new Date().toISOString() }]
      } : null)
      setRxForm({ medicationName: '', dosage: '', frequency: '', duration: '', notes: '' })
      setShowPrescriptionForm(false)
    } catch (err) {
      console.error("Error saving prescription:", err)
      alert("Failed to save prescription.")
    } finally {
      setSavingRx(false)
    }
  }

  const downloadReport = (url: string) => {
    if (url) window.open(url, '_blank', 'noopener,noreferrer')
    else alert('Could not generate a report download link.')
  }

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4">
      <Link href="/doctor/patients" className="inline-flex items-center text-sm text-slate-400 hover:text-blue-400 mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Patients
      </Link>

      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 mb-8 flex flex-col md:flex-row items-center gap-6 shadow-lg">
        <div className="w-20 h-20 rounded-2xl bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0">
          <User className="w-10 h-10" />
        </div>
        <div className="flex-1 text-center md:text-left">
          <h1 className="text-3xl font-bold text-white mb-2">{patient?.fullName || 'Unknown Patient'}</h1>
          <p className="text-slate-400">{patient?.email}</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-slate-950 border border-slate-800 px-4 py-2 rounded-xl text-center">
            <p className="text-xs text-slate-500 uppercase tracking-wider">Age</p>
            <p className="text-lg font-medium text-slate-200">{patient?.age || '--'}</p>
          </div>
          <div className="bg-slate-950 border border-slate-800 px-4 py-2 rounded-xl text-center">
            <p className="text-xs text-slate-500 uppercase tracking-wider">BMI</p>
            <p className="text-lg font-medium text-slate-200">{patient?.bmi || '--'}</p>
          </div>
        </div>
      </div>

      {predictions.length > 0 && (
        <RiskForecastChart patientId={patientId} historicalPredictions={predictions} />
      )}

      {predictions.length >= 2 && (
        <ReportComparison predictions={predictions} />
      )}

      <div className="mb-8">

      </div>

      <div className="mb-12">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-slate-100 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-indigo-400" />
            Prescriptions & Medications
          </h2>
          <button onClick={() => setShowPrescriptionForm(!showPrescriptionForm)} className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center transition-colors">
            <Plus className="w-4 h-4 mr-1" /> Add Prescription
          </button>
        </div>

        {showPrescriptionForm && (
          <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 mb-6">
            <h3 className="text-lg font-medium text-white mb-4">New Prescription</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <input type="text" placeholder="Medication Name" className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-white" value={rxForm.medicationName} onChange={e => setRxForm({...rxForm, medicationName: e.target.value})} />
              <input type="text" placeholder="Dosage (e.g., 50mg)" className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-white" value={rxForm.dosage} onChange={e => setRxForm({...rxForm, dosage: e.target.value})} />
              <input type="text" placeholder="Frequency (e.g., Twice daily)" className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-white" value={rxForm.frequency} onChange={e => setRxForm({...rxForm, frequency: e.target.value})} />
              <input type="text" placeholder="Duration (e.g., 7 days)" className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-white" value={rxForm.duration} onChange={e => setRxForm({...rxForm, duration: e.target.value})} />
              <textarea placeholder="Additional notes..." className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-white md:col-span-2" value={rxForm.notes} onChange={e => setRxForm({...rxForm, notes: e.target.value})} />
            </div>
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowPrescriptionForm(false)} className="px-4 py-2 text-slate-400 hover:text-white">Cancel</button>
              <button onClick={handleSavePrescription} disabled={savingRx} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg flex items-center">
                {savingRx && <Loader2 className="w-4 h-4 mr-2 animate-spin" />} Save Prescription
              </button>
            </div>
          </div>
        )}

        {(!patient?.medications || patient.medications.length === 0) ? (
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 text-center text-slate-500">
            No active prescriptions for this patient.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {patient.medications.map((med, idx) => (
              <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-white font-medium text-lg">{med.medicationName}</h4>
                  {med.createdAt && <span className="text-xs text-slate-500">{new Date(med.createdAt).toLocaleDateString()}</span>}
                </div>
                <div className="grid grid-cols-2 gap-y-2 text-sm">
                  <div><span className="text-slate-500 block text-xs">Dosage</span><span className="text-slate-300">{med.dosage}</span></div>
                  <div><span className="text-slate-500 block text-xs">Frequency</span><span className="text-slate-300">{med.frequency}</span></div>
                  <div><span className="text-slate-500 block text-xs">Duration</span><span className="text-slate-300">{med.duration}</span></div>
                </div>
                {med.notes && <p className="mt-3 text-xs text-slate-400 bg-slate-950 p-2 rounded">{med.notes}</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="mb-12">
        <h2 className="text-xl font-bold text-slate-100 mb-4 flex items-center">
          <MessageSquare className="w-5 h-5 mr-2 text-blue-400" />
          Direct Chat
        </h2>
        {patient && (
          <ChatBox otherUserId={patient.id} otherUserName={patient.fullName || 'Patient'} />
        )}
      </div>

      <h2 className="text-xl font-bold text-slate-100 mb-4 flex items-center">
        <Activity className="w-5 h-5 mr-2 text-emerald-400" />
        Clinical Assessments
      </h2>

      {predictions.length === 0 ? (
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 text-center">
          <p className="text-slate-500">No assessments found for this patient.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {predictions.map(pred => {
            const hasReport = pred.reports && pred.reports.length > 0
            const hasNotes = pred.doctorNotes.length > 0
            
            return (
              <div key={pred.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-md">
                <div className="flex justify-between items-start mb-4 pb-4 border-b border-slate-800">
                  <div>
                    <div className="flex items-center text-slate-400 text-sm mb-2">
                      <Calendar className="w-4 h-4 mr-2" />
                      {new Date(pred.createdAt).toLocaleString()}
                    </div>
                    <h3 className="text-lg font-medium text-white flex items-center gap-3">
                      Risk Score: {(pred.riskScore * 100).toFixed(1)}%
                      <TriageBadge tier={pred.triageTier || 'Green'} />
                    </h3>
                  </div>
                  {hasReport && (
                    <button 
                      onClick={() => downloadReport(pred.reports[0].downloadUrl || '')}
                      className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition-colors flex items-center"
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      View AI Report
                    </button>
                  )}
                </div>

                {pred.streamsUsed?.length && <div className="mb-4 flex flex-wrap gap-2">{pred.streamsUsed.map((stream) => <span key={stream} className="px-2.5 py-1 rounded-full bg-blue-500/10 text-blue-500 text-xs font-semibold">{stream}</span>)}</div>}
                {pred.reports?.[0]?.shapData && <div className="mb-5"><h4 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">Contributing Clinical Factors</h4><div className="grid grid-cols-2 md:grid-cols-3 gap-2">{Object.entries(pred.reports[0].shapData).sort((a,b) => Math.abs(b[1])-Math.abs(a[1])).slice(0,9).map(([feature,value]) => <div key={feature} className="bg-slate-950 border border-slate-800 rounded-xl p-3"><p className="text-xs text-slate-500 truncate">{feature}</p><p className={`font-mono font-semibold mt-1 ${value > 0 ? 'text-red-400' : 'text-emerald-500'}`}>{value.toFixed(4)}</p></div>)}</div></div>}
                {pred.reports?.[0]?.failureAnalysisText && <div className="mb-5 bg-amber-500/5 border border-amber-500/20 rounded-xl p-4"><h4 className="text-sm font-semibold mb-1">Model Analysis</h4><p className="text-sm text-slate-500">{pred.reports[0].failureAnalysisText}</p></div>}
                {pred.reports?.[0]?.interactiveDataUrl ? (
                  <div className="mb-5">
                    <HistoricalEcgViewer interactiveDataUrl={pred.reports[0].interactiveDataUrl} />
                  </div>
                ) : pred.reports?.[0]?.ecgImageUrl ? (
                  <div className="mb-5">
                    <h4 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">ECG Explainability Heatmap</h4>
                    <img src={pred.reports[0].ecgImageUrl} alt="ECG model attention heatmap" className="w-full rounded-2xl border border-slate-800 bg-white" />
                  </div>
                ) : null}
                <ClinicalSummaryCard predictionId={pred.id} />

                {/* Doctor Notes Section */}
                <div className="mt-4">
                  <h4 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">Clinical Notes</h4>
                  
                  {hasNotes ? (
                    <div className="space-y-3 mb-4">
                      {pred.doctorNotes.map((n: DoctorNote, idx: number) => (
                        <div key={idx} className="bg-slate-950 border border-slate-800 p-4 rounded-xl text-slate-300 text-sm">
                          {n.note}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-sm italic mb-4">No notes added yet.</p>
                  )}

                  {activePredictionId === pred.id ? (
                    <div className="space-y-3">
                      <textarea
                        value={noteText}
                        onChange={(e) => setNoteText(e.target.value)}
                        placeholder="Type your clinical observation or recommendation here..."
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl p-4 text-slate-200 text-sm focus:outline-none focus:border-blue-500 min-h-[100px]"
                      />
                      <div className="flex justify-end space-x-3">
                        <button 
                          onClick={() => { setActivePredictionId(null); setNoteText(''); }}
                          className="px-4 py-2 text-slate-400 hover:text-slate-200 text-sm font-medium transition-colors"
                        >
                          Cancel
                        </button>
                        <button 
                          onClick={handleSaveNote}
                          disabled={savingNote || !noteText.trim()}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors flex items-center"
                        >
                          {savingNote && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                          Save Note
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button 
                      onClick={() => setActivePredictionId(pred.id)}
                      className="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center transition-colors"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Add Note
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
