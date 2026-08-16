"use client";

import React, { useEffect, useState } from "react";
import { InteractiveEcgViewer } from "./InteractiveEcgViewer";
import { Loader2 } from "lucide-react";

interface HistoricalEcgViewerProps {
  interactiveDataUrl: string;
}

export function HistoricalEcgViewer({ interactiveDataUrl }: HistoricalEcgViewerProps) {
  const [data, setData] = useState<{ raw_ecg: number[][], ecg_gradcam_data: number[] } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await fetch(interactiveDataUrl);
        if (!res.ok) throw new Error("Failed to fetch interactive ECG data");
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error(err);
        setError("Could not load interactive ECG visualization.");
      }
    }
    fetchData();
  }, [interactiveDataUrl]);

  if (error) {
    return (
      <div className="w-full bg-slate-900 rounded-lg p-4 border border-slate-800 text-slate-400 text-sm text-center flex items-center justify-center h-[300px]">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="w-full bg-slate-900 rounded-lg p-4 border border-slate-800 flex items-center justify-center h-[300px]">
        <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <InteractiveEcgViewer 
      rawEcg={data.raw_ecg} 
      gradCam={data.ecg_gradcam_data} 
    />
  );
}
