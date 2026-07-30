import Dexie, { Table } from 'dexie';
import { PredictRequest, PredictResponse } from './types';

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
 * onnxruntime-web is dynamically imported so it never crashes build workers.
 */
export async function runOfflineInference(request: PredictRequest): Promise<PredictResponse> {
  const modelPath = '/models/vitals_model.onnx';

  try {
    // Dynamic import – only loaded in the browser at call time, never during build
    const ort = await import('onnxruntime-web');
    ort.env.wasm.wasmPaths = '/wasm/';

    const session = await ort.InferenceSession.create(modelPath, { executionProviders: ['wasm'] });

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

    const tensor = new ort.Tensor('float32', inputData, [1, 11]);
    const feeds = { 'input': tensor };
    const results = await session.run(feeds);
    const riskScore = results.output.data[0] as number;

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
    throw new Error("Unable to run offline inference. Please connect to the network for full predictions.");
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
      const payload = { ...item.request, offline_client_id: item.offlineClientId };
      const realResponse = await apiPredictFn(payload);

      await db.predictions.update(item.id!, {
        synced: true,
        response: realResponse
      });
    } catch (e) {
      console.warn(`Failed to sync offline prediction ${item.offlineClientId}`, e);
    }
  }
}
