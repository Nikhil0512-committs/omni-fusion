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
  let cleanKey = key.replace(/^(Vital_|vital_|Hist_|hist_)/i, '').trim();
  const labelMap: Record<string, string> = {
    'creatinine': 'Serum Creatinine',
    'glucose': 'Blood Glucose',
    'potassium': 'Serum Potassium',
    'sodium': 'Serum Sodium',
    'hr': 'Heart Rate (HR)',
    'sbp': 'Systolic BP (SBP)',
    'dbp': 'Diastolic BP (DBP)',
    'rr': 'Respiratory Rate (RR)',
    'o2': 'Oxygen Saturation (O2)',
    'anchor_age': 'Age',
    'gender': 'Gender'
  };

  const keyLower = cleanKey.toLowerCase();
  if (labelMap[keyLower]) return labelMap[keyLower];

  cleanKey = cleanKey.replace(/_/g, ' ');
  return cleanKey.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()).join(' ');
}

export default function ShapWaterfall({ shapData, extractedFields }: ShapWaterfallProps) {
  const map = new Map<string, { name: string; value: number; rawName: string }>();

  Object.entries(shapData).forEach(([name, value]) => {
    if (typeof value !== 'number' || isNaN(value) || Math.abs(value) < 0.0005) return;

    const clean = formatLabel(name);
    if (clean.toLowerCase().includes('offline')) return;

    // Keep feature with highest absolute impact magnitude for each unique formatted label
    const existing = map.get(clean);
    if (!existing || Math.abs(value) > Math.abs(existing.value)) {
      map.set(clean, { name: clean, value, rawName: name });
    }
  });

  const data = Array.from(map.values())
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 6);

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
