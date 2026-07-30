'use client';

interface EcgHeatmapProps {
  base64Image: string;
  failureAnalysis: string;
}

export default function EcgHeatmap({ base64Image, failureAnalysis }: EcgHeatmapProps) {
  return (
    <div className="w-full flex flex-col space-y-4">
      <div className="w-full bg-slate-900 rounded-lg p-4 border border-slate-800">
        <h3 className="text-slate-300 font-semibold mb-4 text-sm">ECG Grad-CAM Thermal Overlay</h3>
        <div className="w-full h-[250px] flex items-center justify-center bg-obsidian rounded overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img 
            src={`data:image/png;base64,${base64Image}`} 
            alt="ECG Heatmap" 
            className="w-full h-full object-contain"
          />
        </div>
      </div>
      
      <div className="w-full bg-slate-900 rounded-lg p-4 border border-slate-800">
        <h3 className="text-slate-300 font-semibold mb-2 text-sm">Automated Analysis Summary</h3>
        <p className="text-slate-400 text-sm leading-relaxed">
          {failureAnalysis}
        </p>
      </div>
    </div>
  );
}
