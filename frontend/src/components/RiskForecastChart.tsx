"use client";

import React, { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Line, ComposedChart } from 'recharts';
import { api } from "@/lib/api";
import { ForecastResponse, StoredPrediction } from "@/lib/types";
import { Loader2, TrendingUp, AlertTriangle } from "lucide-react";

interface RiskForecastChartProps {
  patientId: string;
  historicalPredictions: StoredPrediction[];
}

export function RiskForecastChart({ patientId, historicalPredictions }: RiskForecastChartProps) {
  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadForecast() {
      try {
        const data = await api.getPatientForecast(patientId);
        setForecastData(data);
      } catch (err) {
        console.error("Failed to load forecast", err);
      } finally {
        setLoading(false);
      }
    }
    
    if (historicalPredictions.length > 0) {
      loadForecast();
    } else {
      setLoading(false);
    }
  }, [patientId, historicalPredictions]);

  if (loading) {
    return (
      <div className="w-full h-64 bg-slate-900 border border-slate-800 rounded-3xl flex items-center justify-center shadow-lg">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  // Combine historical and forecast data for the chart
  const chartData: any[] = [];
  
  // Add historical points
  [...historicalPredictions].reverse().forEach(p => {
    chartData.push({
      date: new Date(p.createdAt).toLocaleDateString(),
      timestamp: new Date(p.createdAt).getTime(),
      historicalRisk: p.riskScore * 100,
      isForecast: false
    });
  });

  // Add forecast points if available
  if (forecastData && forecastData.forecast.length > 0) {
    // We want the area to connect from the last historical point
    const lastHistorical = chartData[chartData.length - 1];
    if (lastHistorical) {
      chartData.push({
        date: lastHistorical.date,
        timestamp: lastHistorical.timestamp,
        forecastRisk: lastHistorical.historicalRisk,
        lowerBound: lastHistorical.historicalRisk,
        upperBound: lastHistorical.historicalRisk,
        isForecast: true
      });
    }

    forecastData.forecast.forEach(f => {
      chartData.push({
        date: new Date(f.date).toLocaleDateString(),
        timestamp: new Date(f.date).getTime(),
        forecastRisk: f.projected_risk * 100,
        lowerBound: f.lower_bound * 100,
        upperBound: f.upper_bound * 100,
        isForecast: true
      });
    });
  }

  const hasLowConfidence = forecastData?.confidence === "Low";

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 mb-8 shadow-lg relative overflow-hidden">
      <div className="flex justify-between items-start mb-5">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-purple-400" />
            Longitudinal Risk Forecast
          </h2>
          {forecastData?.message && (
            <p className="text-sm text-slate-400 mt-1">{forecastData.message}</p>
          )}
        </div>
        
        {forecastData && !hasLowConfidence && (
          <div className="bg-slate-950 border border-slate-800 px-3 py-1 rounded-lg flex items-center gap-2">
            <span className="text-xs text-slate-400">Confidence:</span>
            <span className={`text-xs font-semibold ${
              forecastData.confidence === 'High' ? 'text-emerald-400' : 'text-amber-400'
            }`}>
              {forecastData.confidence}
            </span>
          </div>
        )}
      </div>
      
      {hasLowConfidence && forecastData?.forecast.length === 0 ? (
        <div className="h-64 flex flex-col items-center justify-center bg-slate-950/50 rounded-xl border border-slate-800 border-dashed">
          <AlertTriangle className="w-8 h-8 text-amber-500 mb-3 opacity-50" />
          <p className="text-slate-400 text-sm">{forecastData.message}</p>
        </div>
      ) : chartData.length > 0 ? (
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis 
                dataKey="date" 
                stroke="#64748b" 
                fontSize={11} 
                tickMargin={10} 
              />
              <YAxis 
                stroke="#64748b" 
                fontSize={11} 
                domain={[0, 100]} 
                tickFormatter={(val) => `${val}%`}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', borderRadius: '8px' }}
                itemStyle={{ color: '#e2e8f0' }}
                labelStyle={{ color: '#94a3b8', marginBottom: '4px' }}
                formatter={(value: any, name: any) => {
                  if (name === 'historicalRisk') return [`${value.toFixed(1)}%`, 'Historical Risk'];
                  if (name === 'forecastRisk') return [`${value.toFixed(1)}%`, 'Projected Risk'];
                  if (name === 'Range') return [`${value.toFixed(1)}%`, 'Confidence Bounds'];
                  return [value, name];
                }}
              />
              
              {/* Confidence Interval Area */}
              <Area 
                type="monotone" 
                dataKey="upperBound" 
                stroke="none" 
                fill="#8b5cf6" 
                fillOpacity={0.1} 
                activeDot={false}
              />
              <Area 
                type="monotone" 
                dataKey="lowerBound" 
                stroke="none" 
                fill="#0f172a" // Mask out below lower bound
                fillOpacity={1} 
                activeDot={false}
              />

              {/* Historical Line */}
              <Line 
                type="monotone" 
                dataKey="historicalRisk" 
                stroke="#10b981" 
                strokeWidth={3} 
                dot={{ fill: '#10b981', r: 4 }} 
                activeDot={{ r: 6 }}
              />
              
              {/* Forecast Line */}
              <Line 
                type="monotone" 
                dataKey="forecastRisk" 
                stroke="#8b5cf6" 
                strokeWidth={3} 
                strokeDasharray="5 5" 
                dot={{ fill: '#8b5cf6', r: 4 }} 
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="h-64 flex items-center justify-center bg-slate-950/50 rounded-xl">
          <p className="text-slate-500 text-sm">No risk data available to visualize.</p>
        </div>
      )}
    </div>
  );
}
