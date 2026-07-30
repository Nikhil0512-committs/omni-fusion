import React, { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { PredictRequest, PredictResponse } from '@/lib/types';
import { Activity, ArrowRight, Loader2, RefreshCw } from 'lucide-react';
import { TriageBadge } from './TriageBadge';

interface WhatIfExplorerProps {
  baseRequest: PredictRequest;
  originalPrediction: PredictResponse;
}

const VITAL_RANGES = {
  hr: { min: 40, max: 200, step: 1, label: 'Heart Rate (bpm)' },
  sbp: { min: 70, max: 250, step: 1, label: 'Systolic BP (mmHg)' },
  dbp: { min: 40, max: 150, step: 1, label: 'Diastolic BP (mmHg)' },
  rr: { min: 8, max: 40, step: 1, label: 'Resp Rate (bpm)' },
  o2: { min: 70, max: 100, step: 1, label: 'O2 Saturation (%)' },
  glucose: { min: 50, max: 400, step: 1, label: 'Glucose (mg/dL)' },
};

export const WhatIfExplorer: React.FC<WhatIfExplorerProps> = ({ baseRequest, originalPrediction }) => {
  const [overrides, setOverrides] = useState<Record<string, number>>({});
  const [simulatedResult, setSimulatedResult] = useState<PredictResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce the simulation
  useEffect(() => {
    if (Object.keys(overrides).length === 0) {
      setSimulatedResult(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSimulating(true);
      setError(null);
      try {
        const res = await api.runCounterfactualInference({
          base_request: baseRequest,
          overrides
        });
        setSimulatedResult(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Simulation failed');
      } finally {
        setIsSimulating(false);
      }
    }, 600);

    return () => clearTimeout(timer);
  }, [overrides, baseRequest]);

  const handleSliderChange = (vital: string, value: number) => {
    setOverrides(prev => ({
      ...prev,
      [vital]: value
    }));
  };

  const resetOverrides = () => {
    setOverrides({});
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 mt-8 shadow-lg">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-xl font-bold text-slate-100 flex items-center">
          <Activity className="w-5 h-5 mr-2 text-blue-400" />
          Counterfactual Explorer
        </h3>
        {Object.keys(overrides).length > 0 && (
          <button
            onClick={resetOverrides}
            className="flex items-center text-sm text-slate-400 hover:text-slate-200 transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-1" />
            Reset
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Sliders */}
        <div className="space-y-6">
          {Object.entries(VITAL_RANGES).map(([key, config]) => {
            const baseValue = baseRequest.vitals ? baseRequest.vitals[key as keyof typeof baseRequest.vitals] : 0;
            const currentValue = overrides[key] !== undefined ? overrides[key] : baseValue;
            
            return (
              <div key={key}>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-sm font-medium text-slate-300">{config.label}</label>
                  <span className={`text-sm font-mono ${overrides[key] !== undefined ? 'text-blue-400 font-bold' : 'text-slate-500'}`}>
                    {Number(currentValue).toFixed(0)}
                  </span>
                </div>
                <input
                  type="range"
                  min={config.min}
                  max={config.max}
                  step={config.step}
                  value={currentValue}
                  onChange={(e) => handleSliderChange(key, parseFloat(e.target.value))}
                  className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
              </div>
            );
          })}
        </div>

        {/* Results Comparison */}
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 flex flex-col justify-center">
          <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-6 text-center">Impact on Risk Score</h4>
          
          <div className="flex items-center justify-between mb-8">
            <div className="text-center flex-1">
              <p className="text-sm text-slate-500 mb-2">Original</p>
              <p className="text-3xl font-bold text-slate-200">{((originalPrediction.riskScore ?? 0) * 100).toFixed(1)}%</p>
              <div className="mt-2">
                <TriageBadge tier={originalPrediction.triageTier ?? 'Green'} />
              </div>
            </div>
            
            <div className="px-4 text-slate-600 flex items-center justify-center">
              {isSimulating ? <Loader2 className="w-6 h-6 animate-spin text-blue-500" /> : <ArrowRight className="w-6 h-6" />}
            </div>
            
            <div className="text-center flex-1">
              <p className="text-sm text-slate-500 mb-2">Simulated</p>
              {simulatedResult ? (
                <>
                  <p className={`text-3xl font-bold ${(simulatedResult.riskScore ?? 0) > (originalPrediction.riskScore ?? 0) ? 'text-red-400' : 'text-green-400'}`}>
                    {((simulatedResult.riskScore ?? 0) * 100).toFixed(1)}%
                  </p>
                  <div className="mt-2">
                    <TriageBadge tier={simulatedResult.triageTier ?? 'Green'} />
                  </div>
                </>
              ) : (
                <p className="text-3xl font-bold text-slate-700">--</p>
              )}
            </div>
          </div>
          
          {error && (
            <div className="text-sm text-red-400 text-center bg-red-900/20 p-2 rounded">
              {error}
            </div>
          )}
          
          {!simulatedResult && !error && Object.keys(overrides).length === 0 && (
            <p className="text-sm text-slate-500 text-center italic">
              Adjust sliders to simulate changes in patient vitals.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
