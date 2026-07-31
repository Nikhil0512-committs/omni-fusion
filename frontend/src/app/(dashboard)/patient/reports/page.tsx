"use client";

import { useEffect, useState } from 'react'
import { useAuth } from '@/components/auth/AuthProvider'
import { FileText, Download, Calendar, Activity, Loader2, Heart, Beaker, AlertTriangle, ArrowRight, Shield } from 'lucide-react'
import { api } from '@/lib/api'
import type { StoredPrediction } from '@/lib/types'
import Link from 'next/link'

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
    setErrorStr(null)
    try {
      let downloadUrl = url
      if (!downloadUrl) {
        const result = await api.ensureReport(predictionId)
        downloadUrl = result.downloadUrl
        setReports(current => current.map(item => item.id === predictionId ? { ...item, reports: [{ ...(item.reports?.[0] || {id:predictionId,createdAt:item.createdAt,pdfStoragePath:''}), downloadUrl }] } : item))
      }
      if (!downloadUrl) throw new Error('No download URL returned')
      if (downloadUrl.startsWith('data:')) {
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = `Omni-Fusion_Report_${predictionId.slice(0, 8)}.pdf`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      } else {
        window.open(downloadUrl, '_blank', 'noopener,noreferrer')
      }
    } catch (err: any) {
      console.error("PDF Download failed:", err)
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

  // Compute summary stats
  const totalReports = reports.length;
  const avgRisk = totalReports > 0 ? reports.reduce((s, r) => s + (r.riskScore >= 0 ? r.riskScore : 0), 0) / totalReports : 0;
  const highRiskCount = reports.filter(r => r.riskScore > 0.5).length;

  const getRiskColor = (score: number) => {
    if (score > 0.5) return 'text-red-400';
    if (score > 0.2) return 'text-amber-400';
    return 'text-emerald-400';
  };

  const getRiskGradient = (score: number) => {
    if (score > 0.5) return 'from-red-600/20 to-red-900/5';
    if (score > 0.2) return 'from-amber-600/20 to-amber-900/5';
    return 'from-emerald-600/20 to-emerald-900/5';
  };

  const getRiskLabel = (score: number) => {
    if (score < 0) return 'ECG Only';
    if (score > 0.5) return 'High Risk';
    if (score > 0.2) return 'Moderate';
    return 'Low Risk';
  };

  const getRiskBadgeStyle = (score: number) => {
    if (score > 0.5) return 'bg-red-500/15 text-red-400 border-red-500/25';
    if (score > 0.2) return 'bg-amber-500/15 text-amber-400 border-amber-500/25';
    return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25';
  };

  return (
    <div className="p-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">My Reports</h1>
          <p className="text-slate-400">View and download your generated clinical reports.</p>
        </div>
        <Link
          href="/patient/assessment/new"
          className="flex items-center gap-2 px-5 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold rounded-xl text-sm transition-all shadow-lg shadow-emerald-500/15"
        >
          <Activity className="w-4 h-4" />
          New Assessment
        </Link>
      </div>

      {/* Stats Bar */}
      {totalReports > 0 && (
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">Total Reports</p>
              <p className="text-lg font-bold text-white">{totalReports}</p>
            </div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/15 flex items-center justify-center">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">Avg Risk</p>
              <p className={`text-lg font-bold ${getRiskColor(avgRisk)}`}>{(avgRisk * 100).toFixed(1)}%</p>
            </div>
          </div>
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-500/15 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">High Risk</p>
              <p className="text-lg font-bold text-white">{highRiskCount}</p>
            </div>
          </div>
        </div>
      )}

      {errorStr && <div className="service-notice mb-6" role="alert"><Activity className="shrink-0" size={18}/><div><strong>Reports service unavailable</strong><span>{errorStr}</span></div></div>}

      {reports.length === 0 ? (
        <div className="bg-slate-900/50 border border-dashed border-slate-700 rounded-3xl p-16 text-center flex flex-col items-center">
          <div className="w-20 h-20 bg-slate-800/80 rounded-full flex items-center justify-center mb-6 ring-4 ring-slate-800/50">
            <FileText className="w-10 h-10 text-slate-500" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No Reports Yet</h3>
          <p className="text-slate-400 max-w-md mb-6">
            Complete a cardiovascular assessment to generate your first AI-powered clinical report.
          </p>
          <Link
            href="/patient/assessment/new"
            className="flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-sm transition-all shadow-lg shadow-emerald-500/20"
          >
            <Activity className="w-4 h-4" />
            Start Your First Assessment
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {reports.map((pred) => {
            const downloadDoctorNote = (noteText: string, dateStr: string) => {
              const element = document.createElement("a");
              const file = new Blob([`Omni-Fusion Clinical Note\nDate: ${new Date(dateStr).toLocaleString()}\n\n${noteText}`], {type: 'text/plain'});
              element.href = URL.createObjectURL(file);
              element.download = `Doctor_Note_${dateStr.split('T')[0]}.txt`;
              document.body.appendChild(element);
              element.click();
              document.body.removeChild(element);
            };

            const riskPct = pred.riskScore >= 0 ? (pred.riskScore * 100).toFixed(1) : null;

            return (
              <article 
                key={pred.id} 
                className="group bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden hover:border-emerald-500/30 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-emerald-500/5 flex flex-col"
              >
                {/* Gradient Header Strip */}
                <div className={`bg-gradient-to-r ${getRiskGradient(pred.riskScore)} px-6 pt-5 pb-4 border-b border-slate-800/50`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-11 h-11 rounded-2xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center">
                        <Activity className="w-5 h-5 text-emerald-400" />
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-white">Cardiovascular Assessment</h3>
                        <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-0.5">
                          <Calendar className="w-3.5 h-3.5" />
                          {new Date(pred.createdAt).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full border ${getRiskBadgeStyle(pred.riskScore)}`}>
                      {getRiskLabel(pred.riskScore)}
                    </span>
                  </div>
                </div>

                <div className="p-6 flex flex-col flex-1 gap-4">
                  {/* Risk Score Visual */}
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-1.5">Risk Score</p>
                      <div className="flex items-end gap-2">
                        <span className={`text-3xl font-extrabold tracking-tight ${getRiskColor(pred.riskScore)}`}>
                          {riskPct !== null ? `${riskPct}%` : 'N/A'}
                        </span>
                      </div>
                      {/* Mini risk bar */}
                      <div className="mt-2 h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-500 ${
                            pred.riskScore > 0.5 ? 'bg-red-500' : pred.riskScore > 0.2 ? 'bg-amber-500' : 'bg-emerald-500'
                          }`}
                          style={{ width: `${Math.max(pred.riskScore * 100, 2)}%` }}
                        />
                      </div>
                    </div>

                    {/* Streams Used */}
                    {pred.streamsUsed && pred.streamsUsed.length > 0 && (
                      <div className="text-right">
                        <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold mb-1.5">Streams</p>
                        <div className="flex flex-wrap justify-end gap-1">
                          {pred.streamsUsed.map((stream, i) => (
                            <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/50">
                              {stream}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Document Thumbnails */}
                  {(pred.bloodImageUrl || pred.ecgImageUrl) && (
                    <div className="flex gap-3">
                      {pred.bloodImageUrl && (
                        <a 
                          href={pred.bloodImageUrl} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="flex-1 group/thumb"
                        >
                          <p className="text-[10px] text-slate-500 mb-1.5 uppercase tracking-wider font-semibold">Blood Report</p>
                          <div className="relative h-20 rounded-xl border border-slate-700/50 overflow-hidden bg-slate-950 flex items-center justify-center group-hover/thumb:border-emerald-500/40 transition-colors">
                            <img 
                              src={pred.bloodImageUrl} 
                              alt="Blood Report" 
                              className="w-full h-full object-cover opacity-70 group-hover/thumb:opacity-100 transition-opacity" 
                              loading="lazy"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                                const fb = e.currentTarget.parentElement?.querySelector('.img-fb');
                                if (fb) (fb as HTMLElement).style.display = 'flex';
                              }}
                            />
                            <div className="img-fb hidden flex-col items-center justify-center gap-1">
                              <Beaker className="w-5 h-5 text-slate-600" />
                              <span className="text-[9px] text-slate-600">Report analyzed</span>
                            </div>
                          </div>
                        </a>
                      )}
                      {pred.ecgImageUrl && (
                        <a 
                          href={pred.ecgImageUrl} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="flex-1 group/thumb"
                        >
                          <p className="text-[10px] text-slate-500 mb-1.5 uppercase tracking-wider font-semibold">ECG Report</p>
                          <div className="relative h-20 rounded-xl border border-slate-700/50 overflow-hidden bg-slate-950 flex items-center justify-center group-hover/thumb:border-emerald-500/40 transition-colors">
                            <img 
                              src={pred.ecgImageUrl} 
                              alt="ECG Report" 
                              className="w-full h-full object-cover opacity-70 group-hover/thumb:opacity-100 transition-opacity" 
                              loading="lazy"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                                const fb = e.currentTarget.parentElement?.querySelector('.img-fb');
                                if (fb) (fb as HTMLElement).style.display = 'flex';
                              }}
                            />
                            <div className="img-fb hidden flex-col items-center justify-center gap-1">
                              <Heart className="w-5 h-5 text-slate-600" />
                              <span className="text-[9px] text-slate-600">ECG analyzed</span>
                            </div>
                          </div>
                        </a>
                      )}
                    </div>
                  )}

                  {/* ECG Abnormality */}
                  {pred.ecgAbnormality && (
                    <div className="p-3 bg-amber-950/20 border border-amber-800/30 rounded-xl flex items-start gap-2.5">
                      <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                      <div>
                        <p className="text-[11px] text-amber-400 font-semibold mb-0.5">ECG Finding</p>
                        <p className="text-xs text-amber-200/70 line-clamp-2" title={pred.ecgAbnormality}>{pred.ecgAbnormality}</p>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="mt-auto pt-3 grid gap-2">
                    <Link 
                      href={`/patient/reports/${pred.id}`}
                      className="w-full px-4 py-3 bg-emerald-500 hover:bg-emerald-400 text-slate-950 rounded-xl text-sm font-bold transition-all shadow-lg shadow-emerald-500/10 flex items-center justify-center gap-2 group-hover:shadow-emerald-500/20"
                    >
                      <FileText className="w-4 h-4" />
                      View Full Report
                      <ArrowRight className="w-3.5 h-3.5 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                    </Link>

                    {pred.doctorNotes.length > 0 && (
                      <button 
                        onClick={() => downloadDoctorNote(pred.doctorNotes[0].note, pred.doctorNotes[0].createdAt)}
                        className="w-full px-4 py-2.5 bg-slate-800/80 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2 border border-slate-700/50"
                      >
                        <Download className="w-4 h-4" />
                        Doctor&apos;s Notes
                      </button>
                    )}
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
