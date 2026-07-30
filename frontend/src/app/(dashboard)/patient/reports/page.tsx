"use client"

import { useEffect, useState } from 'react'
import { useAuth } from '@/components/auth/AuthProvider'
import { FileText, Download, Calendar, Activity, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import type { StoredPrediction } from '@/lib/types'

export default function PatientReports() {
  const { profile } = useAuth()
  const [reports, setReports] = useState<StoredPrediction[]>([])
  const [loading, setLoading] = useState(true)
  const [errorStr, setErrorStr] = useState<string | null>(null)
  const [preparingId, setPreparingId] = useState<string | null>(null)

  useEffect(() => {
    async function fetchReports() {
      if (!profile) return

      try {
        const predictions = await api.getMyReports()
        setReports(predictions)
      } catch {
        setErrorStr("Reports could not be loaded right now. Please check your connection and try again.")
      } finally {
        setLoading(false)
      }
    }

    fetchReports()
  }, [profile])

  const downloadReport = async (predictionId: string, url?: string) => {
    setPreparingId(predictionId)
    try {
      let downloadUrl = url
      if (!downloadUrl) {
        const result = await api.ensureReport(predictionId)
        downloadUrl = result.downloadUrl
        setReports(current => current.map(item => item.id === predictionId ? { ...item, reports: [{ ...(item.reports?.[0] || {id:predictionId,createdAt:item.createdAt,pdfStoragePath:''}), downloadUrl }] } : item))
      }
      if (!downloadUrl) throw new Error('No download URL returned')
      window.open(downloadUrl, '_blank', 'noopener,noreferrer')
    } catch {
      setErrorStr('This report could not be prepared. Please try again.')
    } finally {
      setPreparingId(null)
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
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">My Reports</h1>
          <p className="text-slate-400">View and download your generated clinical reports.</p>
        </div>
      </div>

      {errorStr && <div className="service-notice mb-6" role="alert"><Activity className="shrink-0" size={18}/><div><strong>Reports service unavailable</strong><span>{errorStr}</span></div></div>}

      {reports.length === 0 ? (
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center">
          <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-slate-400" />
          </div>
          <h3 className="text-xl font-medium text-white mb-2">No Reports Found</h3>
          <p className="text-slate-400 max-w-sm">
            You don't have any generated clinical reports yet. Complete a new assessment to generate one.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reports.map((pred) => {
            const hasReport = pred.reports && pred.reports.length > 0;
            const downloadDoctorNote = (noteText: string, dateStr: string) => {
              const element = document.createElement("a");
              const file = new Blob([`Omni-Fusion Clinical Note\nDate: ${new Date(dateStr).toLocaleString()}\n\n${noteText}`], {type: 'text/plain'});
              element.href = URL.createObjectURL(file);
              element.download = `Doctor_Note_${dateStr.split('T')[0]}.txt`;
              document.body.appendChild(element);
              element.click();
              document.body.removeChild(element);
            };

            return (
              <article key={pred.id} className="bg-slate-900 border border-slate-800 rounded-3xl p-6 hover:border-emerald-500/30 transition-all hover:-translate-y-1 hover:shadow-xl flex flex-col min-h-[290px]">
                  <div className="flex items-start space-x-4">
                    <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center shrink-0">
                      <Activity className="w-6 h-6 text-blue-400" />
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-lg font-medium text-white mb-1">
                        Cardiovascular Assessment
                      </h3>
                      <div className="flex items-center text-sm text-slate-400">
                        <Calendar className="w-4 h-4 mr-1.5" />
                        {new Date(pred.createdAt).toLocaleString()}
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 px-4 py-3 bg-slate-950 rounded-2xl border border-slate-800 flex items-center justify-between">
                      <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Risk Score</p>
                      <p className={`text-lg font-bold ${pred.riskScore > 0.5 ? 'text-red-400' : 'text-emerald-400'}`}>
                        {pred.riskScore >= 0 ? (pred.riskScore * 100).toFixed(1) + '%' : 'N/A (ECG)'}
                      </p>
                  </div>

                  {(pred.bloodImageUrl || pred.ecgImageUrl) && (
                    <div className="mt-4 flex gap-3">
                      {pred.bloodImageUrl && (
                        <div className="flex-1">
                          <p className="text-[10px] text-slate-500 mb-1 uppercase tracking-wider">Blood Report</p>
                          <a href={pred.bloodImageUrl} target="_blank" rel="noopener noreferrer" className="block w-full h-16 rounded-xl border border-slate-700 overflow-hidden hover:border-emerald-500 transition-colors">
                            <img src={pred.bloodImageUrl} alt="Blood Report" className="w-full h-full object-cover opacity-80 hover:opacity-100 transition-opacity" />
                          </a>
                        </div>
                      )}
                      {pred.ecgImageUrl && (
                        <div className="flex-1">
                          <p className="text-[10px] text-slate-500 mb-1 uppercase tracking-wider">ECG Report</p>
                          <a href={pred.ecgImageUrl} target="_blank" rel="noopener noreferrer" className="block w-full h-16 rounded-xl border border-slate-700 overflow-hidden hover:border-emerald-500 transition-colors">
                            <img src={pred.ecgImageUrl} alt="ECG Report" className="w-full h-full object-cover opacity-80 hover:opacity-100 transition-opacity" />
                          </a>
                        </div>
                      )}
                    </div>
                  )}

                  {pred.ecgAbnormality && (
                    <div className="mt-4 p-3 bg-red-900/20 border border-red-800/50 rounded-xl">
                      <p className="text-xs text-red-400 font-semibold mb-1">ECG Abnormality</p>
                      <p className="text-sm text-red-200/80 line-clamp-2" title={pred.ecgAbnormality}>{pred.ecgAbnormality}</p>
                    </div>
                  )}

                    <div className="mt-auto pt-5 grid gap-2">
                        <button 
                          onClick={() => downloadReport(pred.id, hasReport ? pred.reports[0].downloadUrl : undefined)}
                          disabled={preparingId === pred.id}
                          className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-semibold transition-colors flex items-center justify-center disabled:opacity-60"
                        >
                          {preparingId === pred.id ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                          {preparingId === pred.id ? 'Preparing PDF...' : hasReport ? 'Download PDF Report' : 'Generate & Download PDF'}
                        </button>

                      {pred.doctorNotes.length > 0 && (
                        <button 
                          onClick={() => downloadDoctorNote(pred.doctorNotes[0].note, pred.doctorNotes[0].createdAt)}
                          className="w-full px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium transition-colors flex items-center justify-center"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Doctor's Notes
                        </button>
                      )}
                    </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
