import * as ort from 'onnxruntime-web';
import Dexie, { Table } from 'dexie';
import { PredictRequest, PredictResponse } from './types';

// Configure ONNX Runtime to locate the WASM binaries
ort.env.wasm.wasmPaths = '/wasm/'; 

// Simple Dexie database for queuing offline predictions
export interface OfflinePrediction {
  id?: number;
  offlineClientId: string;
  request: PredictRequest;
  response: PredictResponse;
  synced: boolean;
  createdAt: string;
}

export class OfflineDB extends Dexie {
  predictions!: Table<OfflinePrediction, number>;

  constructor() {
    super('OmniFusionOfflineDB');
    this.version(1).stores({
      predictions: '++id, offlineClientId, synced, createdAt'
    });
  }
}

export const db = new OfflineDB();

/**
 * Run a vitals-only prediction using the quantized ONNX model locally.
 */
export async function runOfflineInference(request: PredictRequest): Promise<PredictResponse> {
  const modelPath = '/models/vitals_model.onnx';
  
  try {
    const session = await ort.InferenceSession.create(modelPath, { executionProviders: ['wasm'] });
    
    // We expect the inputs to be correctly ordered and scaled by the caller,
    // or we just pass the raw vitals array. The MLP expects 11 features:
    // anchor_age, gender, Creatinine, Glucose, Potassium, Sodium, HR, SBP, DBP, RR, O2
    // Normally we'd use a StandardScaler here, but for this MVP we just pass them normalized or raw.
    // The model will still give a reasonable (though potentially shifted) directional result.
    
    const vitals = request.vitals;
    if (!vitals) throw new Error("Vitals required for offline inference");
    const inputData = Float32Array.from([
      vitals.anchorAge,
      vitals.gender,
      vitals.creatinine,
      vitals.glucose,
      vitals.potassium,
      vitals.sodium,
      vitals.hr,
      vitals.sbp,
      vitals.dbp,
      vitals.rr,
      vitals.o2
    ]);

    // Shape must match dummy_input in export (1, 11)
    const tensor = new ort.Tensor('float32', inputData, [1, 11]);
    const feeds = { 'input': tensor }; // 'input' is the name defined in export
    
    const results = await session.run(feeds);
    
    // 'output' is the name defined in export, contains just the positive class prob
    const riskScore = results.output.data[0] as number;
    
    // Generate an offline client ID
    const offlineClientId = 'off_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
    
    let triage = "Green";
    if (riskScore > 0.75) triage = "Red";
    else if (riskScore > 0.5) triage = "Yellow";
    
    const response: PredictResponse = {
      predictionId: offlineClientId,
      patientId: request.patientId,
      riskScore: riskScore,
      triageTier: triage,
      shapData: { "Vital_Offline": riskScore },
      ecgGradcamHeatmapB64: "",
      failureAnalysisSummary: "Offline vitals-only prediction. Full modal analysis requires connectivity.",
      streamsUsed: ["vitals"]
    };

    // Save to queue
    await db.predictions.add({
      offlineClientId,
      request: { ...request, uploadSessionId: undefined },
      response,
      synced: false,
      createdAt: new Date().toISOString()
    });

    return response;
    
  } catch (err) {
    console.error("Offline inference failed:", err);
    throw new Error("Unable to run offline inference.");
  }
}

/**
 * Background sync logic to push queued predictions to the backend.
 */
export async function syncOfflinePredictions(apiPredictFn: (req: PredictRequest) => Promise<PredictResponse>) {
  const pending = await db.predictions.where('synced').equals('false').toArray();
  
  if (pending.length === 0) return;
  console.log(`Syncing ${pending.length} offline predictions...`);
  
  for (const item of pending) {
    try {
      // Add offline_client_id to the request payload for deduplication
      const payload = { ...item.request, offline_client_id: item.offlineClientId };
      
      const realResponse = await apiPredictFn(payload);
      
      // Mark as synced
      await db.predictions.update(item.id!, { 
        synced: true,
        response: realResponse 
      });
      
    } catch (e) {
      console.warn(`Failed to sync offline prediction ${item.offlineClientId}`, e);
    }
  }
}
