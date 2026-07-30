"use client";

import React, { useEffect, useRef } from "react";

interface InteractiveEcgViewerProps {
  rawEcg: number[][]; // [12 leads][1000 points]
  gradCam: number[];  // [1000 points]
}

const LEAD_NAMES = [
  "I", "II", "III", "aVR", "aVL", "aVF",
  "V1", "V2", "V3", "V4", "V5", "V6"
];

// Helper to map a value to a color gradient (blue -> white -> red)
function getHeatmapColor(val: number, min: number, max: number): string {
  // Normalize between 0 and 1
  let norm = 0.5;
  if (max > min) {
    norm = (val - min) / (max - min);
  }
  
  // Custom diverging colormap
  if (norm < 0.5) {
    // Blue to Gray/White
    const intensity = Math.floor((norm * 2) * 255);
    return `rgb(${intensity}, ${intensity}, 255)`;
  } else {
    // Gray/White to Red
    const intensity = Math.floor((1 - (norm - 0.5) * 2) * 255);
    return `rgb(255, ${intensity}, ${intensity})`;
  }
}

export function InteractiveEcgViewer({ rawEcg, gradCam }: InteractiveEcgViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !rawEcg || rawEcg.length === 0 || !gradCam || gradCam.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Handle high DPI displays
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    // Set actual size in memory (scaled to account for extra pixel density)
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    
    // Normalize coordinate system to use css pixels
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;

    // Clear background
    ctx.fillStyle = "#ffffff"; // white background for ECG
    ctx.fillRect(0, 0, width, height);

    // Draw grid
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 10) {
      ctx.strokeStyle = x % 50 === 0 ? "rgba(255, 100, 100, 0.4)" : "rgba(255, 100, 100, 0.1)";
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += 10) {
      ctx.strokeStyle = y % 50 === 0 ? "rgba(255, 100, 100, 0.4)" : "rgba(255, 100, 100, 0.1)";
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // 4 columns, 3 rows for standard 12-lead layout
    const cols = 4;
    const rows = 3;
    const cellWidth = width / cols;
    const cellHeight = height / rows;

    // Find min and max for Grad-CAM normalization
    let gcMin = Math.min(...gradCam);
    let gcMax = Math.max(...gradCam);
    // Add small epsilon to prevent division by zero
    if (gcMax === gcMin) gcMax += 0.0001;

    for (let leadIdx = 0; leadIdx < 12; leadIdx++) {
      if (!rawEcg[leadIdx]) continue;

      const row = leadIdx % rows;
      const col = Math.floor(leadIdx / rows);
      
      const offsetX = col * cellWidth;
      const offsetY = row * cellHeight;

      // Draw lead label
      ctx.fillStyle = "#000000";
      ctx.font = "bold 12px Arial";
      ctx.fillText(LEAD_NAMES[leadIdx], offsetX + 10, offsetY + 20);

      // We only draw 1/4th of the 1000 points per column cell (roughly 2.5 seconds)
      // Standard 10-second ECG has 2.5s per column in the 4x3 layout
      const ptsPerCell = Math.floor(1000 / cols);
      const startIdx = col * ptsPerCell;
      
      const leadData = rawEcg[leadIdx].slice(startIdx, startIdx + ptsPerCell);
      const leadGrad = gradCam.slice(startIdx, startIdx + ptsPerCell);

      const dx = cellWidth / leadData.length;
      const centerY = offsetY + cellHeight / 2;
      const yScale = 20; // arbitrary scale for visualization

      // Draw segments so we can color them individually based on Grad-CAM
      ctx.lineWidth = 1.5;
      
      for (let i = 0; i < leadData.length - 1; i++) {
        const x1 = offsetX + i * dx;
        const y1 = centerY - leadData[i] * yScale;
        const x2 = offsetX + (i + 1) * dx;
        const y2 = centerY - leadData[i + 1] * yScale;

        const gradVal = leadGrad[i];
        ctx.strokeStyle = getHeatmapColor(gradVal, gcMin, gcMax);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.stroke();
      }
    }
  }, [rawEcg, gradCam]);

  return (
    <div className="w-full bg-white rounded-lg shadow border border-slate-200 overflow-hidden">
      <div className="p-3 border-b border-slate-100 flex justify-between items-center bg-slate-50">
        <h3 className="font-semibold text-slate-700">Interactive 12-Lead ECG</h3>
        <div className="flex items-center text-xs text-slate-500 gap-2">
          <span>AI Attention:</span>
          <div className="w-32 h-3 rounded bg-gradient-to-r from-blue-500 via-gray-300 to-red-500" />
        </div>
      </div>
      <div className="p-4 w-full h-[500px] relative">
        <canvas
          ref={canvasRef}
          style={{ width: "100%", height: "100%" }}
          className="rounded border border-red-100"
        />
      </div>
    </div>
  );
}
