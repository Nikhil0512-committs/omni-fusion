'use client';

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

interface ShapWaterfallProps {
  shapData: Record<string, number>;
  extractedFields?: string[];
}

function formatLabel(key: string): string {
  let formatted = key.replace(/^(Vital_|vital_|Hist_|hist_)/i, '');
  formatted = formatted.replace(/_/g, ' ');
  const acronyms = ['hr', 'sbp', 'dbp', 'rr', 'o2'];
  return formatted.split(' ').map(word => {
    if (acronyms.includes(word.toLowerCase())) {
      return word.toUpperCase();
    }
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }).join(' ');
}

export default function ShapWaterfall({ shapData, extractedFields }: ShapWaterfallProps) {
  // Convert dict to sorted array
  const reportBiomarkers = ['creatinine', 'glucose', 'potassium', 'sodium', 'anchor_age', 'gender'];
  
  const data = Object.entries(shapData)
    .map(([name, value]) => {
      const clean = formatLabel(name);
      const isReportMetric = reportBiomarkers.some(b => name.toLowerCase().includes(b)) || 
        (extractedFields && extractedFields.some(f => name.toLowerCase().includes(f.toLowerCase())));
      return { name: clean, value, rawName: name, isReportMetric };
    })
    .sort((a, b) => {
      // Prioritize extracted lab biomarkers
      if (a.isReportMetric && !b.isReportMetric) return -1;
      if (!a.isReportMetric && b.isReportMetric) return 1;
      return Math.abs(b.value) - Math.abs(a.value);
    })
    .slice(0, 10);

  return (
    <div className="w-full h-[320px] bg-slate-900 rounded-lg p-4 border border-slate-800 flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-slate-100 font-bold text-base">Risk Factor Impact Analysis (SHAP)</h3>
        <div className="flex items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1 text-emerald-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" /> Lowers Risk
          </span>
          <span className="flex items-center gap-1 text-red-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-red-500 inline-block" /> Increases Risk
          </span>
        </div>
      </div>
      <p className="text-xs text-slate-400 mb-3">Feature importance calculated across extracted patient report biomarkers.</p>
      
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 0, right: 30, left: 45, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
            <XAxis type="number" stroke="#94a3b8" fontSize={11} />
            <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} width={85} />
            <Tooltip 
              contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc', borderRadius: '8px' }}
              cursor={{fill: '#334155', opacity: 0.4}}
              formatter={(val: any) => [
                `${Number(val) > 0 ? '+' : ''}${Number(val).toFixed(4)} (${Number(val) > 0 ? 'Increases Risk' : 'Protective / Lowers Risk'})`, 
                "SHAP Value"
              ]}
            />
            <Bar dataKey="value">
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#ef4444' : '#3b82f6'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
