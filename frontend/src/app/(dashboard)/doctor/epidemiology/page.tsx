"use client"

import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { Activity, Map as MapIcon, Loader2 } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'

// Simulated coordinates for districts/pincodes to render the heatmap
// In a real app, you would use a geocoding service.
const LOCATION_COORDS: Record<string, [number, number]> = {
  "Delhi": [28.6139, 77.2090],
  "Mumbai": [19.0760, 72.8777],
  "Bangalore": [12.9716, 77.5946],
  "Chennai": [13.0827, 80.2707],
  "Kolkata": [22.5726, 88.3639],
  "Hyderabad": [17.3850, 78.4867],
  "Pune": [18.5204, 73.8567],
  "Ahmedabad": [23.0225, 72.5714],
  "Jaipur": [26.9124, 75.7873],
  "Unknown": [20.5937, 78.9629] // Center of India
};

interface HeatmapData {
  location: string;
  average_risk: number;
  sample_size: number;
}

export default function EpidemiologyMap() {
  const [data, setData] = useState<HeatmapData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchHeatmap() {
      try {
        const supabase = createClient()
        const { data: sessionData } = await supabase.auth.getSession()
        
        const res = await fetch(process.env.NEXT_PUBLIC_API_BASE_URL + '/api/v1/epidemiology/heatmap', {
          headers: {
            'Authorization': `Bearer ${sessionData.session?.access_token}`
          }
        })
        
        if (!res.ok) {
          throw new Error('Failed to fetch epidemiology data')
        }
        
        const json = await res.json()
        setData(json.data)
      } catch (err) {
        console.error(err)
        setError('Failed to load epidemiology heatmap')
      } finally {
        setLoading(false)
      }
    }
    fetchHeatmap()
  }, [])

  return (
    <main className="min-h-screen p-8 md:p-12 flex flex-col items-center">
      <div className="w-full max-w-6xl space-y-8 animate-in fade-in slide-in-from-bottom-4">
        
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-emerald-900/40 border border-emerald-800 rounded-xl shadow-lg text-emerald-400">
              <MapIcon className="w-8 h-8" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-slate-50">Epidemiological Heatmap</h1>
              <p className="text-slate-400 mt-1">Real-time cardiovascular risk surveillance across regions</p>
            </div>
          </div>
        </header>

        {error && (
          <div className="bg-red-900/30 border border-red-800 text-red-200 p-4 rounded-lg">
            {error}
          </div>
        )}

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden h-[600px] flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-slate-100 flex items-center">
              <Activity className="w-5 h-5 mr-2 text-blue-400" />
              Regional Risk Distribution
            </h2>
            <div className="flex space-x-4 text-xs font-medium text-slate-400">
              <span className="flex items-center text-xs text-slate-400"><span className="w-3 h-3 rounded-full bg-red-500 mr-2 opacity-70"></span> High Risk (&gt; 0.5)</span>
              <span className="flex items-center text-xs text-slate-400"><span className="w-3 h-3 rounded-full bg-yellow-500 mr-2 opacity-70"></span> Moderate (0.2 - 0.5)</span>
              <span className="flex items-center text-xs text-slate-400"><span className="w-3 h-3 rounded-full bg-green-500 mr-2 opacity-70"></span> Low Risk (&lt; 0.2)</span>
            </div>
          </div>

          <div className="flex-1 rounded-xl overflow-hidden border border-slate-700 relative bg-slate-950">
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center">
                <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              </div>
            ) : (
              <MapContainer 
                center={[20.5937, 78.9629]} 
                zoom={5} 
                style={{ height: '100%', width: '100%', background: '#09090b' }}
                scrollWheelZoom={false}
              >
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
                />
                
                {data.map((item, i) => {
                  const coords = LOCATION_COORDS[item.location] || [
                    20.5937 + (Math.random() - 0.5) * 5, 
                    78.9629 + (Math.random() - 0.5) * 5
                  ];
                  
                  const color = item.average_risk > 0.5 ? '#ef4444' : item.average_risk > 0.2 ? '#eab308' : '#22c55e';
                  
                  return (
                    <CircleMarker
                      key={i}
                      center={coords}
                      pathOptions={{ fillColor: color, color: color, weight: 1, fillOpacity: 0.6 }}
                      radius={Math.max(10, Math.min(30, item.sample_size * 5))}
                    >
                      <Tooltip direction="top" offset={[0, -10]} opacity={1} className="custom-tooltip">
                        <div className="p-1">
                          <div className="font-bold border-b border-slate-200 pb-1 mb-1">{item.location}</div>
                          <div className="text-sm">Avg Risk: {(item.average_risk * 100).toFixed(1)}%</div>
                          <div className="text-sm">Patients: {item.sample_size}</div>
                        </div>
                      </Tooltip>
                    </CircleMarker>
                  );
                })}
              </MapContainer>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
