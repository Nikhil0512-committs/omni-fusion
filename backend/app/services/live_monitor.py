import asyncio
import neurokit2 as nk
import numpy as np
from datetime import datetime, timezone

class LiveMonitorService:
    def __init__(self, patient_id: str, sampling_rate: int = 100, base_hr: float = 75.0, base_spo2: float = 98.0, base_sbp: float = 120.0, base_dbp: float = 80.0):
        self.patient_id = patient_id
        self.sampling_rate = sampling_rate
        self.hr = base_hr
        self.spo2 = base_spo2
        self.sbp = base_sbp
        self.dbp = base_dbp
        self.time_offset = 0.0

    async def generate_stream(self, chunk_duration_sec: float = 1.0):
        """Yields chunks of simulated vitals."""
        while True:
            # Random walk for vitals
            self.hr += np.random.normal(0, 1)
            self.hr = np.clip(self.hr, 50, 150)
            
            # 5% chance of SpO2 dropping to simulate an anomaly, but then recovering
            if np.random.random() < 0.05:
                self.spo2 -= np.random.uniform(2, 5)
            else:
                self.spo2 += np.random.normal(0, 0.5)
            self.spo2 = np.clip(self.spo2, 85, 100)
            
            self.sbp += np.random.normal(0, 2)
            self.sbp = np.clip(self.sbp, 90, 180)
            
            self.dbp += np.random.normal(0, 1)
            self.dbp = np.clip(self.dbp, 50, 110)

            # Generate ECG segment using neurokit2
            try:
                ecg = nk.ecg_simulate(
                    duration=chunk_duration_sec, 
                    sampling_rate=self.sampling_rate, 
                    heart_rate=int(self.hr)
                )
            except Exception:
                # Fallback if generation fails
                ecg = np.zeros(int(chunk_duration_sec * self.sampling_rate))
                
            # Convert to list for JSON serialization
            ecg_list = ecg.tolist()
            
            yield {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "hr": round(self.hr, 1),
                "spo2": round(self.spo2, 1),
                "bp": f"{int(self.sbp)}/{int(self.dbp)}",
                "ecg": ecg_list,
                "is_anomaly": bool(self.spo2 < 90.0)
            }
            
            self.time_offset += chunk_duration_sec
            await asyncio.sleep(chunk_duration_sec)
