"use client";

import React, { useState, useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';

interface ClinicalSummaryCardProps {
  predictionId: string;
}

export const ClinicalSummaryCard: React.FC<ClinicalSummaryCardProps> = ({ predictionId }) => {
  const [summary, setSummary] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setIsLoading(true);
        const supabase = createClient();
        const { data: sessionData } = await supabase.auth.getSession();
        
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
        };
        if (sessionData.session?.access_token) {
          headers['Authorization'] = `Bearer ${sessionData.session.access_token}`;
        }
        
        const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${baseUrl}/api/v1/copilot/summarize`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ prediction_id: predictionId }),
        });

        if (!response.ok) {
          throw new Error('Failed to generate summary');
        }

        const summaryData = await response.json();
        setSummary(summaryData.soap_note);
      } catch (err) {
        setError('GenAI Clinical Co-Pilot is currently unavailable. Please rely on the raw metrics provided.');
      } finally {
        setIsLoading(false);
      }
    };

    if (predictionId && predictionId !== 'counterfactual_sim') {
      fetchSummary();
    } else {
      setIsLoading(false);
      setError('GenAI Clinical Co-Pilot requires a saved prediction.');
    }
  }, [predictionId]);

  const handleCopy = () => {
    if (summary) {
      navigator.clipboard.writeText(summary);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6 animate-pulse mt-6">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          <div className="h-3 bg-gray-200 rounded w-full"></div>
          <div className="h-3 bg-gray-200 rounded w-5/6"></div>
          <div className="h-3 bg-gray-200 rounded w-4/6"></div>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mt-6">
        <p className="text-sm text-yellow-800">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6 mt-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg leading-6 font-medium text-gray-900">AI Clinical Summary (SOAP)</h3>
        <button
          onClick={handleCopy}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          {copied ? 'Copied!' : 'Copy for EHR'}
        </button>
      </div>
      <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
        {summary}
      </div>
    </div>
  );
};
