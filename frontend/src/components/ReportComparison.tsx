"use client"

import React, { useState } from 'react'
import { StoredPrediction } from '@/lib/types'
import { ArrowRight, Activity, Calendar } from 'lucide-react'
import { TriageBadge } from '@/components/TriageBadge'

export function ReportComparison({ predictions }: { predictions: StoredPrediction[] }) {
  const [selected1, setSelected1] = useState<string | null>(predictions[0]?.id || null)
  const [selected2, setSelected2] = useState<string | null>(predictions.length > 1 ? predictions[1]?.id : null)

  if (predictions.length < 2) {
    return null
  }

  const p1 = predictions.find(p => p.id === selected1)
  const p2 = predictions.find(p => p.id === selected2)

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 mb-8 shadow-lg">
      <h2 className="text-xl font-bold text-slate-100 mb-6 flex items-center">
        <Activity className="w-5 h-5 mr-2 text-blue-400" />
        Compare Assessments
      </h2>

      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="flex-1">
          <label className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">Assessment A</label>
          <select 
            value={selected1 || ''} 
            onChange={(e) => setSelected1(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
          >
            {predictions.map(p => (
              <option key={p.id} value={p.id}>
                {new Date(p.createdAt).toLocaleString()} - Risk: {(p.riskScore * 100).toFixed(1)}%
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1">
          <label className="text-xs text-slate-500 uppercase tracking-wider mb-2 block">Assessment B</label>
          <select 
            value={selected2 || ''} 
            onChange={(e) => setSelected2(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-slate-200 text-sm focus:outline-none focus:border-blue-500"
          >
            {predictions.map(p => (
              <option key={p.id} value={p.id}>
                {new Date(p.createdAt).toLocaleString()} - Risk: {(p.riskScore * 100).toFixed(1)}%
              </option>
            ))}
          </select>
        </div>
      </div>

      {p1 && p2 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center bg-slate-950/50 p-6 rounded-2xl border border-slate-800">
          
          <div className="text-center">
            <h3 className="text-sm font-semibold text-slate-400 mb-2">Assessment A</h3>
            <div className="text-2xl font-bold text-white mb-2">{(p1.riskScore * 100).toFixed(1)}%</div>
            <TriageBadge tier={p1.triageTier || 'Green'} />
          </div>

          <div className="flex flex-col items-center justify-center">
            <div className="text-sm text-slate-500 mb-1">Difference</div>
            <div className="flex items-center gap-3">
              <ArrowRight className="w-5 h-5 text-slate-600" />
              <div className={`text-xl font-bold ${p2.riskScore > p1.riskScore ? 'text-red-400' : 'text-emerald-400'}`}>
                {((p2.riskScore - p1.riskScore) * 100).toFixed(1)}%
              </div>
            </div>
          </div>

          <div className="text-center">
            <h3 className="text-sm font-semibold text-slate-400 mb-2">Assessment B</h3>
            <div className="text-2xl font-bold text-white mb-2">{(p2.riskScore * 100).toFixed(1)}%</div>
            <TriageBadge tier={p2.triageTier || 'Green'} />
          </div>

        </div>
      )}
    </div>
  )
}
