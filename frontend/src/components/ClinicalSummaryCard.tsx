"use client";

import React, { useState, useEffect } from 'react';
import { createClient } from '@/lib/supabase/client';
import { Sparkles, Copy, Check, FileText, Activity, Stethoscope, AlertTriangle, ShieldCheck } from 'lucide-react';

interface ClinicalSummaryCardProps {
  predictionId: string;
}

interface ParsedSoapSection {
  title: string;
  key: 'subjective' | 'objective' | 'assessment' | 'plan';
  items: string[];
}

function parseMarkdownText(text: string): React.ReactNode[] {
  return text.split('\n').map((line, idx) => {
    let trimmed = line.trim();
    if (!trimmed) return null;

    // Handle headers
    if (trimmed.startsWith('# ')) {
      return (
        <h3 key={idx} className="text-lg font-bold text-slate-100 mt-3 mb-2 border-b border-slate-800 pb-1">
          {trimmed.replace('# ', '')}
        </h3>
      );
    }
    if (trimmed.startsWith('## ')) {
      return (
        <h4 key={idx} className="text-sm font-bold uppercase tracking-wider text-emerald-400 mt-4 mb-2 flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
          {trimmed.replace('## ', '')}
        </h4>
      );
    }
    if (trimmed.startsWith('### ')) {
      return (
        <h5 key={idx} className="text-xs font-semibold text-slate-300 mt-2 mb-1">
          {trimmed.replace('### ', '')}
        </h5>
      );
    }

    // Handle bullet items
    const isBullet = trimmed.startsWith('- ') || trimmed.startsWith('* ');
    if (isBullet) {
      trimmed = trimmed.replace(/^[\-\*]\s+/, '');
    }

    // Format bold text **word**
    const parts = trimmed.split(/(\*\*.*?\*\*)/g);
    const content = parts.map((part, pIdx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={pIdx} className="font-semibold text-slate-100">
            {part.slice(2, -2)}
          </strong>
        );
      }
      return part;
    });

    if (isBullet) {
      return (
        <li key={idx} className="text-sm text-slate-300 leading-relaxed ml-4 list-disc marker:text-emerald-400 my-1">
          {content}
        </li>
      );
    }

    return (
      <p key={idx} className="text-sm text-slate-300 leading-relaxed my-1">
        {content}
      </p>
    );
  });
}

function parseSoapSections(rawSoap: string): ParsedSoapSection[] {
  const sections: ParsedSoapSection[] = [];
  const lines = rawSoap.split('\n');
  let currentSection: ParsedSoapSection | null = null;

  lines.forEach(line => {
    const trimmed = line.trim();
    const lower = trimmed.toLowerCase();

    if (lower.includes('subjective')) {
      if (currentSection) sections.push(currentSection);
      currentSection = { title: 'Subjective (S)', key: 'subjective', items: [] };
    } else if (lower.includes('objective')) {
      if (currentSection) sections.push(currentSection);
      currentSection = { title: 'Objective (O)', key: 'objective', items: [] };
    } else if (lower.includes('assessment')) {
      if (currentSection) sections.push(currentSection);
      currentSection = { title: 'Assessment (A)', key: 'assessment', items: [] };
    } else if (lower.includes('plan')) {
      if (currentSection) sections.push(currentSection);
      currentSection = { title: 'Plan & Recommendations (P)', key: 'plan', items: [] };
    } else if (currentSection && trimmed) {
      if (!trimmed.startsWith('#')) {
        currentSection.items.push(trimmed);
      }
    }
  });

  if (currentSection) sections.push(currentSection);
  return sections;
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
      <div className="w-full bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 animate-pulse mt-6">
        <div className="flex items-center justify-between">
          <div className="h-6 bg-slate-800 rounded w-1/3"></div>
          <div className="h-8 bg-slate-800 rounded w-24"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-32 bg-slate-850 rounded-xl"></div>
          <div className="h-32 bg-slate-850 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="w-full bg-amber-950/30 border border-amber-800/60 rounded-2xl p-5 mt-6 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <p className="text-sm text-amber-200/90 leading-relaxed font-medium">{error}</p>
      </div>
    );
  }

  const parsedSections = parseSoapSections(summary);
  const sectionColors = {
    subjective: { border: 'border-sky-800/40', bg: 'bg-sky-950/30', text: 'text-sky-300', icon: Stethoscope },
    objective: { border: 'border-emerald-800/40', bg: 'bg-emerald-950/30', text: 'text-emerald-300', icon: Activity },
    assessment: { border: 'border-amber-800/40', bg: 'bg-amber-950/30', text: 'text-amber-300', icon: ShieldCheck },
    plan: { border: 'border-purple-800/40', bg: 'bg-purple-950/30', text: 'text-purple-300', icon: FileText }
  };

  return (
    <div className="w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl mt-6 space-y-5">
      {/* Top Bar Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800/80 gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-md">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-bold text-white tracking-tight">AI Clinical Summary (SOAP)</h3>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                Concise High-Yield Note
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">Automated clinical documentation & guideline-backed synthesis.</p>
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="flex items-center justify-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-100 px-4 py-2 rounded-xl text-xs font-semibold border border-slate-700 transition-all shadow-sm active:scale-95 shrink-0"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-bold">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5 text-slate-400" />
              <span>Copy for EHR</span>
            </>
          )}
        </button>
      </div>

      {/* Structured SOAP Sections Grid */}
      {parsedSections.length >= 2 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {parsedSections.map((sec) => {
            const config = sectionColors[sec.key] || sectionColors.subjective;
            const IconComp = config.icon;
            return (
              <div key={sec.key} className={`rounded-xl border ${config.border} ${config.bg} p-4 flex flex-col space-y-2.5 shadow-sm`}>
                <div className="flex items-center space-x-2 border-b border-slate-800/80 pb-2">
                  <IconComp className={`w-4 h-4 ${config.text} shrink-0`} />
                  <h4 className={`text-xs font-bold uppercase tracking-wider ${config.text}`}>
                    {sec.title}
                  </h4>
                </div>
                <ul className="space-y-2 pt-0.5">
                  {sec.items.map((item, i) => (
                    <li key={i} className="text-xs text-slate-200 leading-relaxed font-normal flex items-start gap-2">
                      <span className={`w-1.5 h-1.5 rounded-full ${config.text} shrink-0 mt-1.5 bg-current opacity-90`} />
                      <span className="flex-1">{parseMarkdownText(item)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      ) : (
        /* Fallback rich formatted text box if unstructured */
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-5 space-y-2 text-slate-200">
          {parseMarkdownText(summary)}
        </div>
      )}
    </div>
  );
};
