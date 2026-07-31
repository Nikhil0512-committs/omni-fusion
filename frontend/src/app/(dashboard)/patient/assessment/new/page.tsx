'use client';

import { useState, useEffect } from 'react';
import { Activity, Download, ChevronRight, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import FileUploadZone from '@/components/FileUploadZone';
import HistoryTimeline from '@/components/HistoryTimeline';
import ShapWaterfall from '@/components/ShapWaterfall';
import { WhatIfExplorer } from '@/components/WhatIfExplorer';
import { TriageBadge } from '@/components/TriageBadge';
import { ClinicalSummaryCard } from '@/components/ClinicalSummaryCard';
import { api } from '@/lib/api';
import { PredictResponse, ReportResponse, PredictRequest, VitalsInput } from '@/lib/types';
import Link from 'next/link';
import { useAuth } from '@/components/auth/AuthProvider';
import { runOfflineInference, syncOfflinePredictions } from '@/lib/offlineInference';

export default function Dashboard() {
  const { user, profile } = useAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [ecgSessionId, setEcgSessionId] = useState<string | null>(null);
  const [ecgAbnormality, setEcgAbnormality] = useState<string | null>(null);
  const [bloodImagePath, setBloodImagePath] = useState<string | null>(null);
  const [ecgImagePath, setEcgImagePath] = useState<string | null>(null);
  const [ecgPreviewUrl, setEcgPreviewUrl] = useState<string | null>(null);
  
  const [historicalData, setHistoricalData] = useState<VitalsInput | null>(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);
  const [report, setReport] = useState<ReportResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<{ createdAt: string, riskScore: number }[]>([]);
  const [baseRequest, setBaseRequest] = useState<PredictRequest | null>(null);
  
  useEffect(() => {
    async function loadHistory() {
      try {
        const hist = await api.getHistory(20, 0);
        setHistoryData(hist.items.map(item => ({ createdAt: item.createdAt, riskScore: item.riskScore })));
      } catch (err) {
        console.error("Failed to load history:", err);
      }
    }
    loadHistory();

    const handleOnline = () => {
      console.log("Back online. Syncing offline predictions...");
      syncOfflinePredictions(api.runClinicalInference.bind(api)).catch(console.error);
    };
    window.addEventListener('online', handleOnline);
    
    // Sync immediately if we are online on mount
    if (typeof navigator !== 'undefined' && navigator.onLine) {
      handleOnline();
    }
    
    return () => window.removeEventListener('online', handleOnline);
  }, []);

  const handleRunInference = async () => {
    setIsPredicting(true);
    setError(null);
    try {
      // Fetch realistic 12-lead ECG from the backend demo endpoint
      let ecgData = Array(12).fill(Array(1000).fill(0));
      try {
        const demoRes = await fetch((process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '/api/v1/demo-ecg');
        if (demoRes.ok) {
          const json = await demoRes.json();
          ecgData = json.ecg;
        }
      } catch (e) {
        console.error("Failed to fetch demo ECG, falling back to dummy", e);
        ecgData = Array(12).fill(0).map((_, i) => 
          Array(1000).fill(0).map((_, j) => Math.sin(j * 0.05 + i) * 0.5 + (Math.random() * 0.2))
        );
      }

      // Extract vitals from historical if available, with robust fallback for camelCase and uppercase keys
      const dummyVitals = {
        anchorAge: (historicalData as any)?.anchorAge ?? (historicalData as any)?.anchor_age ?? 45.0,
        gender: (historicalData as any)?.gender ?? 1,
        creatinine: (historicalData as any)?.creatinine ?? (historicalData as any)?.Creatinine ?? 1.1,
        glucose: (historicalData as any)?.glucose ?? (historicalData as any)?.Glucose ?? 95.0,
        potassium: (historicalData as any)?.potassium ?? (historicalData as any)?.Potassium ?? 4.2,
        sodium: (historicalData as any)?.sodium ?? (historicalData as any)?.Sodium ?? 140.0,
        hr: (historicalData as any)?.hr ?? (historicalData as any)?.HR ?? 72.0,
        sbp: (historicalData as any)?.sbp ?? (historicalData as any)?.SBP ?? 120.0,
        dbp: (historicalData as any)?.dbp ?? (historicalData as any)?.DBP ?? 80.0,
        rr: (historicalData as any)?.rr ?? (historicalData as any)?.RR ?? 14.0,
        o2: (historicalData as any)?.o2 ?? (historicalData as any)?.O2 ?? 99.0
      };

      const isEcgOnly = sessionId === null && ecgSessionId !== null;

      const payload: PredictRequest = {
        patientId: profile?.id || user?.id || "",
        ecg: ecgData,
        vitals: dummyVitals,
        historical: historicalData || undefined,
        uploadSessionId: sessionId || ecgSessionId || undefined,
        isEcgOnly,
        bloodImagePath: bloodImagePath || undefined,
        ecgImagePath: ecgImagePath || undefined,
        ecgAbnormality: ecgAbnormality || undefined
      };

      setBaseRequest(payload);

      let pred: PredictResponse;
      try {
        // Attempt online prediction
        pred = await api.runClinicalInference(payload);
        
        // Attempt instant report generation independently
        try {
          const rep = await api.generateReport(pred.predictionId, {
            patientId: payload.patientId,
            shapData: pred.shapData,
            ecgGradcamHeatmapB64: pred.ecgGradcamHeatmapB64 || "",
            failureAnalysisSummary: pred.failureAnalysisSummary,
            ecgGradcamData: pred.ecgGradcamData,
            rawEcg: pred.rawEcg
          });
          setReport(rep);
        } catch (repErr) {
          console.warn("Report generation notice:", repErr);
        }
      } catch (onlineErr) {
        console.error("Online inference error:", onlineErr);
        throw onlineErr;
      }

      setPrediction(pred);

    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to run inference');
    } finally {
      setIsPredicting(false);
    }
  };

  return (
    <main className="min-h-screen p-8 md:p-12 flex flex-col items-center">
      <div className="w-full max-w-6xl">
        <header className="flex items-center justify-between mb-12">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl shadow-lg">
              <Activity className="w-8 h-8 text-slate-100" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-50">Omni-Fusion Dashboard</h1>
              <p className="text-slate-400 mt-1">Multimodal Patient Risk Assessment</p>
            </div>
          </div>
          <Link href="/history" className="flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition-colors">
            <FileText className="w-5 h-5" />
            <span className="font-medium">View History</span>
          </Link>
        </header>

        {error && (
          <div className="w-full bg-red-900/30 border border-red-800 text-red-200 p-4 rounded-lg mb-8">
            {error}
          </div>
        )}

        {/* Top Section: Upload & Action */}
        <section className="w-full mb-12 bg-obsidian border border-slate-800 rounded-2xl p-8 shadow-2xl flex flex-col md:flex-row items-stretch justify-between gap-8">
          <div className="flex-1 w-full space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-200 mb-2">1. Blood Report / Historical Data</h2>
              <p className="text-slate-500 text-sm mb-4">Upload a blood report to calculate cardiovascular risk.</p>
              <FileUploadZone mode="blood" onSessionCreated={(res) => {
                setSessionId(res.sessionId);
                if (res.aggregatedData) {
                  setHistoricalData(res.aggregatedData);
                  if (res.aggregatedData.uploadedImagePath) setBloodImagePath(res.aggregatedData.uploadedImagePath);
                }
              }} />
            </div>
            
            <div className="border-t border-slate-800 pt-6">
              <h2 className="text-lg font-semibold text-slate-200 mb-2">2. ECG Report (Optional)</h2>
              <p className="text-slate-500 text-sm mb-4">Upload a 12-lead ECG printout for Vision AI extraction.</p>
              <FileUploadZone mode="ecg" onSessionCreated={(res, previewUrl) => {
                setEcgSessionId(res.sessionId);
                if (previewUrl) setEcgPreviewUrl(previewUrl);
                if (res.aggregatedData) {
                  if (res.aggregatedData.ecgAbnormality) setEcgAbnormality(res.aggregatedData.ecgAbnormality);
                  if (res.aggregatedData.uploadedImagePath) setEcgImagePath(res.aggregatedData.uploadedImagePath);
                }
              }} />
            </div>
          </div>
          
          <div className="hidden md:flex flex-col items-center justify-center px-4">
            <ChevronRight className="w-8 h-8 text-slate-700" />
          </div>

          <div className="flex-1 w-full flex flex-col items-center justify-center border-t md:border-t-0 md:border-l border-slate-800 pt-8 md:pt-0 pl-0 md:pl-8">
            <h2 className="text-lg font-semibold text-slate-200 mb-4">3. Run AI Model</h2>
            <button
              onClick={handleRunInference}
              disabled={isPredicting}
              className={`px-8 py-4 rounded-xl font-bold text-lg flex items-center space-x-2 transition-all ${
                isPredicting 
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-slate-100 text-slate-900 hover:bg-white hover:shadow-xl hover:shadow-white/10'
              }`}
            >
              {isPredicting ? (
                <span>Processing Streams...</span>
              ) : (
                <>
                  <Activity className="w-5 h-5" />
                  <span>Execute Multimodal Inference</span>
                </>
              )}
            </button>
            {(sessionId || ecgSessionId) && !isPredicting && (
              <p className="text-green-400 text-sm mt-4">Data attached. Ready.</p>
            )}
          </div>
        </section>

        {/* Results Section */}
        {prediction && (
          <section className="w-full grid grid-cols-1 lg:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Left Viewport */}
            <div className="flex flex-col space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  {prediction.riskScore !== null ? (
                    <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
                      Risk Score: <span className={prediction.riskScore > 0.5 ? 'text-red-400' : 'text-green-400'}>{(prediction.riskScore * 100).toFixed(1)}%</span>
                      {prediction.triageTier && <TriageBadge tier={prediction.triageTier} />}
                    </h2>
                  ) : (
                    <h2 className="text-2xl font-bold text-amber-400 flex items-center gap-3">
                      ECG Only Analysis - No Risk Score
                    </h2>
                  )}
                  <p className="text-slate-500 text-sm mt-1">Streams combined: {prediction.streamsUsed.join(' + ')}</p>
                </div>
                {report && (
                  <a 
                    href={report.pdfSignedUrl}
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 px-4 py-2 rounded-lg transition-colors border border-slate-700"
                  >
                    <Download className="w-4 h-4" />
                    <span className="text-sm font-medium">PDF Report</span>
                  </a>
                )}
              </div>
              {report && (
                <div className="service-notice report-saved-notice">
                  <CheckCircle className="shrink-0" size={18} />
                  <div>
                    <strong>Report saved to your medical history</strong>
                    <span>Generated {new Date().toLocaleString()} · You can download it anytime from <Link href="/patient/reports" className="underline">Reports</Link>.</span>
                  </div>
                </div>
              )}
              
              {ecgSessionId && prediction.ecgAbnormality && (
                <div className="w-full bg-red-900/20 border border-red-800 rounded-lg p-4 mb-4">
                  <h3 className="text-red-400 font-semibold mb-1 text-sm flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" /> ECG Findings Extracted
                  </h3>
                  <p className="text-red-200/80 text-sm">
                    {prediction.ecgAbnormality}
                  </p>
                  <p className="text-red-300 text-xs mt-2 font-medium">Please consult a doctor for further evaluation.</p>
                </div>
              )}
              
              {prediction.riskScore !== null && <ShapWaterfall shapData={prediction.shapData} />}
              
              <div className="w-full bg-slate-900 rounded-lg p-4 border border-slate-800">
                <h3 className="text-slate-300 font-semibold mb-4 text-sm">Longitudinal Medical History</h3>
                <HistoryTimeline data={historyData} />
              </div>
            </div>

            {/* Right Viewport: User Uploaded ECG Report Document / Image */}
            <div className="flex flex-col space-y-4">
              {(ecgSessionId || ecgPreviewUrl) && ecgPreviewUrl && (
                <div className="w-full bg-slate-900 rounded-xl p-5 border border-slate-800 flex flex-col gap-4 shadow-xl">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
                      Uploaded ECG Report Document
                    </span>
                    <a 
                      href={ecgPreviewUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-xs text-slate-400 hover:text-emerald-400 flex items-center gap-1 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" /> View Original
                    </a>
                  </div>

                  <div className="relative w-full h-[360px] rounded-lg overflow-hidden bg-slate-950 border border-slate-800/80 flex items-center justify-center">
                    {ecgPreviewUrl.toLowerCase().endsWith('.pdf') || ecgPreviewUrl.startsWith('blob:') ? (
                      <iframe 
                        src={ecgPreviewUrl} 
                        title="User Uploaded ECG Document" 
                        className="w-full h-full border-none rounded-lg"
                      />
                    ) : (
                      <img 
                        src={ecgPreviewUrl} 
                        alt="User Uploaded ECG" 
                        className="w-full h-full object-contain" 
                      />
                    )}
                  </div>
                </div>
              )}
              
              <div className="w-full bg-slate-900 rounded-lg p-4 border border-slate-800">
                <h3 className="text-slate-300 font-semibold mb-2 text-sm">Automated Analysis Summary</h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  {prediction.failureAnalysisSummary}
                </p>
              </div>

              {prediction.riskScore !== null && <ClinicalSummaryCard predictionId={prediction.predictionId} />}
            </div>
            
            {/* Full width What-If Explorer */}
            {baseRequest && (
              <div className="lg:col-span-2">
                <WhatIfExplorer baseRequest={baseRequest} originalPrediction={prediction} />
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
