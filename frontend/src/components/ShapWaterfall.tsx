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
}

function formatLabel(key: string): string {
  let formatted = key.replace(/^(Vital_|vital_)/i, '');
  formatted = formatted.replace(/_/g, ' ');
  const acronyms = ['hr', 'sbp', 'dbp', 'rr', 'o2'];
  return formatted.split(' ').map(word => {
    if (acronyms.includes(word.toLowerCase())) {
      return word.toUpperCase();
    }
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  }).join(' ');
}

export default function ShapWaterfall({ shapData }: ShapWaterfallProps) {
  // Convert dict to sorted array by absolute magnitude
  const data = Object.entries(shapData)
    .map(([name, value]) => ({ name: formatLabel(name), value, rawName: name }))
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
    .slice(0, 10); // Top 10 features

  return (
    <div className="w-full h-[300px] bg-slate-900 rounded-lg p-4 border border-slate-800">
      <h3 className="text-slate-100 font-bold mb-4 text-lg">Risk Factor Impact Analysis (SHAP)</h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={data}
          margin={{ top: 0, right: 30, left: 40, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
          <XAxis type="number" stroke="#94a3b8" fontSize={12} />
          <YAxis dataKey="name" type="category" stroke="#94a3b8" fontSize={11} width={80} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
            cursor={{fill: '#334155', opacity: 0.4}}
            formatter={(value: any) => [Number(value).toFixed(4), "Impact"]}
          />
          <Bar dataKey="value">
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#ef4444' : '#3b82f6'} /> // red for risk+, blue for risk-
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
