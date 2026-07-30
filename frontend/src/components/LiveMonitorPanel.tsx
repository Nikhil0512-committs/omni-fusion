"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { AlertCircle, Activity, Heart, Droplet, Wind } from "lucide-react";

interface LiveMonitorProps {
  patientId: string;
}

interface StreamFrame {
  timestamp: string;
  hr: number;
  spo2: number;
  bp: string;
  ecg: number[];
  is_anomaly: boolean;
}

export function LiveMonitorPanel({ patientId }: LiveMonitorProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alertMsg, setAlertMsg] = useState<string | null>(null);
  const [currentVitals, setCurrentVitals] = useState<{
    hr: number;
    spo2: number;
    bp: string;
  } | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const ecgBufferRef = useRef<number[]>([]);
  const animationFrameRef = useRef<number | null>(null);
  const drawIndexRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Constants for canvas drawing
  const MAX_POINTS = 500; // number of points to show on screen at once
  const Y_OFFSET = 75; // vertical center for ECG
  const Y_SCALE = 30; // height scaling for ECG

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // We consume a few points per frame to smoothly animate
    const pointsToConsume = 4; // adjust speed
    const newPoints = ecgBufferRef.current.splice(0, pointsToConsume);
    
    if (newPoints.length === 0) {
      // Nothing to draw right now, just loop
      animationFrameRef.current = requestAnimationFrame(draw);
      return;
    }

    const width = canvas.width;
    const height = canvas.height;

    // Background fade effect for moving trace
    ctx.fillStyle = "rgba(15, 23, 42, 0.1)"; // tail fade
    ctx.fillRect(0, 0, width, height);

    ctx.lineWidth = 2;
    ctx.strokeStyle = "#10b981"; // emerald green for ECG
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    ctx.beginPath();
    let x = drawIndexRef.current;
    let y = Y_OFFSET - newPoints[0] * Y_SCALE;
    
    // Starting point is from the last known x,y, but we don't have it explicitly stored.
    // We'll just draw the new points
    ctx.moveTo(x, y);

    for (let i = 1; i < newPoints.length; i++) {
      x += width / MAX_POINTS;
      if (x > width) {
        x = 0; // wrap around
        // Clear a bit ahead of the drawing head
        ctx.clearRect(x, 0, 50, height);
        ctx.moveTo(x, y);
      }
      y = Y_OFFSET - newPoints[i] * Y_SCALE;
      ctx.lineTo(x, y);
    }
    
    ctx.stroke();
    drawIndexRef.current = x;

    animationFrameRef.current = requestAnimationFrame(draw);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Assuming backend is at localhost:8000 for local dev or relative path
    const wsUrl = process.env.NEXT_PUBLIC_API_BASE_URL 
      ? `${process.env.NEXT_PUBLIC_API_BASE_URL.replace("http", "ws")}/api/v1/live-monitor/${patientId}?token=dummy`
      : `${protocol}//localhost:8000/api/v1/live-monitor/${patientId}?token=dummy`;
    
    console.log("Connecting to websocket:", wsUrl);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("Live monitor connected");
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "ALERT") {
          setAlertMsg(data.message);
          setTimeout(() => setAlertMsg(null), 5000);
          return;
        }

        const frame = data as StreamFrame;
        setCurrentVitals({
          hr: frame.hr,
          spo2: frame.spo2,
          bp: frame.bp,
        });

        // Add ECG data to buffer
        if (frame.ecg && Array.isArray(frame.ecg)) {
          ecgBufferRef.current.push(...frame.ecg);
        }
      } catch (err) {
        console.error("Error parsing websocket message", err);
      }
    };

    ws.onclose = () => {
      console.log("Live monitor disconnected");
      setIsConnected(false);
      // Reconnect logic
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    };

    ws.onerror = (err) => {
      console.error("Websocket error", err);
      setError("Connection error. Retrying...");
      ws.close();
    };
  }, [patientId]);

  useEffect(() => {
    connect();
    
    // Setup canvas
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext("2d");
      if (ctx) {
        ctx.fillStyle = "#0f172a"; // slate-900
        ctx.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      }
    }
    
    // Start animation loop
    animationFrameRef.current = requestAnimationFrame(draw);

    return () => {
      console.log("Live monitor unmounting, cleaning up");
      if (wsRef.current) {
        // Remove onclose to prevent reconnect loop during unmount
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [connect, draw]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl relative flex flex-col">
      <div className="p-4 border-b border-slate-800 flex justify-between items-center bg-slate-950/50">
        <div className="flex items-center gap-3">
          <Activity className="w-5 h-5 text-emerald-400" />
          <h3 className="font-semibold text-slate-200">Real-Time IoT Telemetry</h3>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2.5 h-2.5 rounded-full ${isConnected ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`} />
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            {isConnected ? "Live stream active" : "Reconnecting..."}
          </span>
        </div>
      </div>
      
      {alertMsg && (
        <div className="absolute top-16 left-4 right-4 z-10">
          <div className="bg-red-950/90 border border-red-900 text-red-200 animate-in fade-in slide-in-from-top-4 p-4 rounded-lg flex items-start gap-3 shadow-lg">
            <AlertCircle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
            <div className="flex flex-col">
              <h4 className="font-semibold text-red-300">Critical Threshold Breached</h4>
              <p className="text-sm opacity-90">{alertMsg}</p>
            </div>
          </div>
        </div>
      )}

      {error && !isConnected && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-10">
          <p className="text-red-400 font-medium">{error}</p>
        </div>
      )}

      <div className="relative h-[200px] w-full p-4">
        {/* The canvas is absolutely positioned to fill the space for drawing */}
        <canvas 
          ref={canvasRef} 
          width={800} 
          height={150} 
          className="w-full h-full rounded bg-slate-900"
        />
        
        {/* Overlay grid lines (optional visual flair) */}
        <div className="absolute inset-4 pointer-events-none opacity-20" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
      </div>

      <div className="grid grid-cols-3 divide-x divide-slate-800 border-t border-slate-800 bg-slate-950/50">
        <div className="p-4 flex flex-col items-center justify-center">
          <div className="flex items-center gap-2 text-slate-400 mb-1">
            <Heart className="w-4 h-4 text-rose-500" />
            <span className="text-xs uppercase tracking-wider font-semibold">HR</span>
          </div>
          <div className="text-3xl font-bold text-slate-200">
            {currentVitals?.hr || "--"} <span className="text-sm font-normal text-slate-500">bpm</span>
          </div>
        </div>
        
        <div className="p-4 flex flex-col items-center justify-center">
          <div className="flex items-center gap-2 text-slate-400 mb-1">
            <Droplet className="w-4 h-4 text-cyan-500" />
            <span className="text-xs uppercase tracking-wider font-semibold">SpO2</span>
          </div>
          <div className={`text-3xl font-bold ${currentVitals?.spo2 && currentVitals.spo2 < 90 ? "text-red-500 animate-pulse" : "text-cyan-400"}`}>
            {currentVitals?.spo2 || "--"} <span className="text-sm font-normal text-slate-500">%</span>
          </div>
        </div>

        <div className="p-4 flex flex-col items-center justify-center">
          <div className="flex items-center gap-2 text-slate-400 mb-1">
            <Wind className="w-4 h-4 text-indigo-400" />
            <span className="text-xs uppercase tracking-wider font-semibold">NIBP</span>
          </div>
          <div className="text-3xl font-bold text-slate-200">
            {currentVitals?.bp || "--"} <span className="text-sm font-normal text-slate-500">mmHg</span>
          </div>
        </div>
      </div>
    </div>
  );
}
