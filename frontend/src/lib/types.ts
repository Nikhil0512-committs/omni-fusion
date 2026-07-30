export interface VitalsInput {
  anchorAge: number; gender: number; creatinine: number; glucose: number;
  potassium: number; sodium: number; hr: number; sbp: number; dbp: number;
  rr: number; o2: number;
}

export type HistoricalInput = VitalsInput;

export interface Prescription {
  id: string;
  medicationName: string;
  dosage: string;
  frequency: string;
  duration: string;
  notes?: string;
  createdAt?: string;
}

export interface ChatMessage {
  id: string;
  sender_id: string;
  receiver_id: string;
  content: string;
  read: boolean;
  created_at: string;
}

export interface PredictRequest {
  patientId: string;
  ecg: number[][];
  vitals?: VitalsInput;
  historical?: HistoricalInput;
  uploadSessionId?: string;
  offlineClientId?: string;
  isEcgOnly?: boolean;
  bloodImagePath?: string;
  ecgImagePath?: string;
  ecgAbnormality?: string;
}

export interface PredictResponse {
  predictionId: string; patientId: string; riskScore: number | null;
  triageTier: string | null; shapData: Record<string, number>;
  ecgGradcamHeatmapB64: string | null; failureAnalysisSummary: string;
  streamsUsed: string[];
  ecgGradcamData?: number[];
  rawEcg?: number[][];
  ecgAbnormality?: string | null;
}

export interface PredictCounterfactualRequest {
  base_request: PredictRequest;
  overrides: Record<string, number>;
}

export interface UploadHistoricalResponse {
  sessionId: string; rowCount: number; imputationSummary: Record<string, any>;
  status: string; aggregatedData?: any;
}

export interface ReportRequest {
  patientId: string; shapData: Record<string, number>;
  ecgGradcamHeatmapB64: string; failureAnalysisSummary: string;
  ecgGradcamData?: number[];
  rawEcg?: number[][];
}

export interface ReportResponse {
  predictionId: string; riskScore: number; shapData: Record<string, number>;
  failureAnalysisText: string; pdfStoragePath: string; pdfSignedUrl: string;
}

export interface HistoryItem {
  predictionId: string; createdAt: string; riskScore: number;
  triageTier?: string; streamsUsed: string[]; hasReport: boolean;
}
export interface HistoryResponse { items: HistoryItem[]; total: number }

export interface Profile {
  id: string; role: 'PATIENT' | 'DOCTOR'; fullName?: string; email?: string;
  age?: number; bmi?: number; smokingStatus?: string; specialization?: string;
  hospital?: string; phone?: string; medications?: Prescription[];
}
export interface ProfileInput extends Omit<Profile, 'id'> {
  dateOfBirth?: string | null; sex?: string; heightCm?: number | null;
  weightKg?: number | null; alcoholUse?: string; exerciseFrequency?: string;
  medicalRegistrationNumber?: string; bio?: string;
}

export interface ForecastPoint {
  date: string;
  projected_risk: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResponse {
  forecast: ForecastPoint[];
  confidence: "Low" | "Medium" | "High";
  message: string;
}

export interface AnalyticsTrend { createdAt: string; riskScore: number }
export interface ClinicalAnalytics {
  trends?: AnalyticsTrend[]; averageRisk?: number; highestRisk?: number;
  totalPatients?: number; averageRiskAll?: number; highRiskPatients?: number;
  riskDistribution?: { low: number, medium: number, high: number };
  topPatients?: { patientId: string, name: string, email: string, riskScore: number, lastAssessment: string }[];
}
export interface DoctorProfile extends Profile { role: 'DOCTOR' }
export interface DoctorPatientLink { id: string; patientId: string; doctorId: string; status: 'pending' | 'accepted' | 'rejected'; createdAt: string; profiles: Profile; latest_triage_tier?: string }
export interface DoctorNote { id: string; note: string; createdAt: string; priority?: string }
export interface StoredReport { id: string; createdAt: string; pdfStoragePath: string; downloadUrl?: string; shapData?: Record<string, number>; failureAnalysisText?: string; interactiveDataUrl?: string; ecgImageUrl?: string; bloodImageUrl?: string; }
export interface StoredPrediction { id: string; createdAt: string; riskScore: number; triageTier?: string; streamsUsed?: string[]; reports: StoredReport[]; doctorNotes: DoctorNote[]; raw_ecg?: number[]; ecg_gradcam_data?: number[]; bloodImageUrl?: string; ecgImageUrl?: string; ecgAbnormality?: string }
export interface PatientRecord { profile: Profile; predictions: StoredPrediction[] }
export interface DoctorConnection { message: string; doctor: DoctorProfile }
