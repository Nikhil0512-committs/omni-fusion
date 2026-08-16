'use client';

import { useEffect, useState } from 'react';
import { FileText, ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { HistoryResponse } from '@/lib/types';
import { TriageBadge } from '@/components/TriageBadge';

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await api.getHistory(20, 0);
        setHistory(res);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : 'Failed to load history');
      } finally {
        setLoading(false);
      }
    }
    loadHistory();
  }, []);

  return (
    <main className="min-h-screen p-8 md:p-12 flex flex-col items-center">
      <div className="w-full max-w-5xl">
        <header className="flex items-center justify-between mb-12 border-b border-slate-800 pb-8">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-slate-900 border border-slate-800 rounded-xl">
              <FileText className="w-8 h-8 text-slate-100" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-50">Prediction History</h1>
              <p className="text-slate-400 mt-1">Review past patient assessments</p>
            </div>
          </div>
          <Link href="/" className="flex items-center space-x-2 text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Back to Dashboard</span>
          </Link>
        </header>

        {loading && (
          <div className="flex flex-col items-center py-20">
            <Loader2 className="w-8 h-8 text-slate-500 animate-spin mb-4" />
            <p className="text-slate-400">Loading records...</p>
          </div>
        )}

        {error && (
          <div className="w-full bg-red-900/30 border border-red-800 text-red-200 p-4 rounded-lg flex items-center space-x-3">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {!loading && !error && history && (
          <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-obsidian text-slate-400 text-sm border-b border-slate-800">
                  <th className="p-4 font-medium">Date</th>
                  <th className="p-4 font-medium">Prediction ID</th>
                  <th className="p-4 font-medium">Risk Score</th>
                  <th className="p-4 font-medium">Streams Used</th>
                  <th className="p-4 font-medium text-right">Report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50 text-sm">
                {history.items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-slate-500">
                      No past predictions found.
                    </td>
                  </tr>
                ) : (
                  history.items.map((item) => (
                    <tr key={item.predictionId} className="hover:bg-slate-800/50 transition-colors">
                      <td className="p-4 text-slate-300">
                        {new Date(item.createdAt).toLocaleString()}
                      </td>
                      <td className="p-4 text-slate-500 font-mono text-xs">
                        {item.predictionId.split('-')[0]}...
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          item.riskScore > 0.5 ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                        } mr-2`}>
                          {(item.riskScore * 100).toFixed(1)}%
                        </span>
                        <TriageBadge tier={item.triageTier || 'Green'} />
                      </td>
                      <td className="p-4 text-slate-400">
                        {item.streamsUsed.join(', ')}
                      </td>
                      <td className="p-4 text-right">
                        {/* Note: the history item model doesn't return the signed url directly because they expire. 
                            Ideally, we'd have a specific /api/v1/report/url endpoint. 
                            For this demo, we'll assume they need to generate a new report if they want to view it, 
                            or we can just show a placeholder if we didn't implement url generation on GET. */}
                        {item.hasReport ? (
                          <span className="text-slate-500 italic text-xs">Stored</span>
                        ) : (
                          <span className="text-slate-600 text-xs">-</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
