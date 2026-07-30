import {
  UploadHistoricalResponse,
  PredictCounterfactualRequest, PredictRequest,
  PredictResponse,
  ReportRequest,
  ReportResponse,
  HistoryResponse,
  ForecastResponse,
  ClinicalAnalytics, DoctorConnection, DoctorPatientLink, PatientRecord, Profile,
  ProfileInput, StoredPrediction, VitalsInput, ChatMessage,
} from './types';

export type Notification = {
  id: string;
  userId: string;
  title: string;
  message: string;
  type: string;
  read: boolean;
  createdAt: string;
};

export type PaginatedNotifications = {
  items: Notification[];
  total: number;
  unreadCount: number;
};

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

import { createClient } from './supabase/client';

type SnakeVitals = { anchor_age:number; gender:number; Creatinine:number; Glucose:number; Potassium:number; Sodium:number; HR:number; SBP:number; DBP:number; RR:number; O2:number };
type RawPrediction = { prediction_id:string; patient_id:string; risk_score:number|null; shap_data:Record<string,number>; ecg_gradcam_heatmap_b64:string|null; ecg_gradcam_data?:number[]; raw_ecg?:number[][]; failure_analysis_summary:string; streams_used:string[]; ecg_abnormality?:string|null; triage_tier?:string|null };
type RawUpload = { session_id:string; row_count:number; imputation_summary:Record<string,any>; status:string; aggregated_data?:any };
type RawReportResponse = { prediction_id:string; risk_score:number|null; shap_data:Record<string,number>; failure_analysis_text:string; pdf_storage_path:string; pdf_signed_url:string };
type RawStoredPrediction = { id:string; created_at:string; risk_score:number; streams_used?:string[]; blood_image_url?:string; ecg_image_url?:string; ecg_abnormality?:string; reports?:Array<{id:string;created_at:string;pdf_storage_path:string;download_url?:string;shap_data?:Record<string,number>;failure_analysis_text?:string;ecg_image_url?:string;interactive_data_url?:string}>; doctor_notes?:Array<{id:string;note:string;created_at:string;priority?:string}> };
type RawProfile = Record<string, unknown> & { id:string; role:'PATIENT'|'DOCTOR' };
type RawLink = { id:string; patient_id:string; doctor_id:string; status:'pending'|'accepted'|'rejected'; created_at:string; profiles:RawProfile; latest_triage_tier?:string };

const mapVitalsToWire = (value: VitalsInput): SnakeVitals => ({ anchor_age:value.anchorAge,gender:value.gender,Creatinine:value.creatinine,Glucose:value.glucose,Potassium:value.potassium,Sodium:value.sodium,HR:value.hr,SBP:value.sbp,DBP:value.dbp,RR:value.rr,O2:value.o2 });
const mapVitalsFromWire = (value: any): any => ({ anchorAge:value.anchor_age,gender:value.gender,creatinine:value.Creatinine,glucose:value.Glucose,potassium:value.Potassium,sodium:value.Sodium,hr:value.HR,sbp:value.SBP,dbp:value.DBP,rr:value.RR,o2:value.O2, uploadedImagePath: value.uploaded_image_path, ecgAbnormality: value.ecg_abnormality });
const mapPredictRequest = (value: PredictRequest) => ({ patient_id:value.patientId,ecg:value.ecg,vitals:value.vitals?mapVitalsToWire(value.vitals):undefined,historical:value.historical?mapVitalsToWire(value.historical):undefined,upload_session_id:value.uploadSessionId,offline_client_id:value.offlineClientId,is_ecg_only:value.isEcgOnly,blood_image_path:value.bloodImagePath,ecg_image_path:value.ecgImagePath,ecg_abnormality:value.ecgAbnormality });

const WIRE_VITAL_MAP: Record<string, string> = {
  anchorAge: 'anchor_age',
  gender: 'gender',
  creatinine: 'Creatinine',
  glucose: 'Glucose',
  potassium: 'Potassium',
  sodium: 'Sodium',
  hr: 'HR',
  sbp: 'SBP',
  dbp: 'DBP',
  rr: 'RR',
  o2: 'O2'
};

const mapCounterfactualRequest = (value: PredictCounterfactualRequest) => {
  const mappedOverrides: Record<string, number> = {};
  for (const [k, v] of Object.entries(value.overrides)) {
    mappedOverrides[WIRE_VITAL_MAP[k] || k] = v;
  }
  return { 
    base_request: mapPredictRequest(value.base_request), 
    overrides: mappedOverrides 
  };
};
const mapPredictionResponse = (raw: RawPrediction): PredictResponse => ({ predictionId:raw.prediction_id,patientId:raw.patient_id,riskScore:raw.risk_score,triageTier: raw.triage_tier || null, shapData:raw.shap_data,ecgGradcamHeatmapB64:raw.ecg_gradcam_heatmap_b64,ecgGradcamData:raw.ecg_gradcam_data,rawEcg:raw.raw_ecg,failureAnalysisSummary:raw.failure_analysis_summary,streamsUsed:raw.streams_used,ecgAbnormality:raw.ecg_abnormality });
const mapProfile = (raw: RawProfile): Profile => ({ id:raw.id,role:raw.role,fullName:raw.full_name as string|undefined,email:raw.email as string|undefined,age:raw.age as number|undefined,bmi:raw.bmi as number|undefined,smokingStatus:raw.smoking_status as string|undefined,specialization:raw.specialization as string|undefined,hospital:raw.hospital as string|undefined,phone:raw.phone as string|undefined,medications:(raw.medications as any) || [] });
const mapProfileInput = (value: ProfileInput) => ({ role:value.role,full_name:value.fullName,email:value.email,date_of_birth:value.dateOfBirth,sex:value.sex,height_cm:value.heightCm,weight_kg:value.weightKg,smoking_status:value.smokingStatus,alcohol_use:value.alcoholUse,exercise_frequency:value.exerciseFrequency,medical_registration_number:value.medicalRegistrationNumber,specialization:value.specialization,hospital:value.hospital,phone:value.phone,bio:value.bio });
const mapStoredPrediction = (raw: RawStoredPrediction): StoredPrediction => ({ id:raw.id,createdAt:raw.created_at,riskScore:raw.risk_score,streamsUsed:raw.streams_used,bloodImageUrl:(raw as any).blood_image_url,ecgImageUrl:(raw as any).ecg_image_url,ecgAbnormality:(raw as any).ecg_abnormality,reports:(raw.reports||[]).map(item=>({id:item.id,createdAt:item.created_at,pdfStoragePath:item.pdf_storage_path,downloadUrl:item.download_url,shapData:item.shap_data,failureAnalysisText:item.failure_analysis_text,ecgImageUrl:item.ecg_image_url,interactiveDataUrl:item.interactive_data_url})),doctorNotes:(raw.doctor_notes||[]).map(item=>({id:item.id,note:item.note,createdAt:item.created_at,priority:item.priority})) });

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    
    // Inject auth token if available
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    const headers = new Headers(options.headers || {});
    
    if (data.session?.access_token) {
      headers.set('Authorization', `Bearer ${data.session.access_token}`);
    }
    
    const fetchOptions = { ...options, headers };
    const response = await fetch(url, fetchOptions);

    if (!response.ok) {
      let errorMessage = `API error: ${response.statusText}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorMessage;
      } catch {
        // Fallback to basic text if not JSON
      }
      throw new Error(errorMessage);
    }

    return response.json() as Promise<T>;
  }

  async uploadHistoricalCSV(file: File): Promise<UploadHistoricalResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const raw = await this.request<RawUpload>('/api/v1/upload-historical', {
      method: 'POST',
      body: formData,
    });
    return {sessionId:raw.session_id,rowCount:raw.row_count,imputationSummary:raw.imputation_summary,status:raw.status,aggregatedData:raw.aggregated_data?mapVitalsFromWire(raw.aggregated_data):undefined};
  }

  async uploadBloodReport(file: File): Promise<UploadHistoricalResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const raw = await this.request<RawUpload>('/api/v1/upload-blood-report', {
      method: 'POST',
      body: formData,
    });
    return {sessionId:raw.session_id,rowCount:raw.row_count,imputationSummary:raw.imputation_summary,status:raw.status,aggregatedData:raw.aggregated_data?mapVitalsFromWire(raw.aggregated_data):undefined};
  }

  async uploadEcgReport(file: File): Promise<UploadHistoricalResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const raw = await this.request<RawUpload>('/api/v1/upload-ecg-report', {
      method: 'POST',
      body: formData,
    });
    return {sessionId:raw.session_id,rowCount:raw.row_count,imputationSummary:raw.imputation_summary,status:raw.status,aggregatedData:raw.aggregated_data?mapVitalsFromWire(raw.aggregated_data):undefined};
  }

  async runInference(payload: PredictRequest): Promise<PredictResponse> {
    const raw = await this.request<RawPrediction>('/api/v1/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(mapPredictRequest(payload)),
    });
    return mapPredictionResponse(raw);
  }

  async runCounterfactualInference(payload: PredictCounterfactualRequest): Promise<PredictResponse> {
    const raw = await this.request<RawPrediction>('/api/v1/predict/counterfactual', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(mapCounterfactualRequest(payload)),
    });
    return mapPredictionResponse(raw);
  }

  async generateReport(predictionId: string, payload: ReportRequest): Promise<ReportResponse> {
    const raw = await this.request<RawReportResponse>(`/api/v1/report/${predictionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({patient_id:payload.patientId,shap_data:payload.shapData,ecg_gradcam_heatmap_b64:payload.ecgGradcamHeatmapB64,failure_analysis_summary:payload.failureAnalysisSummary,ecg_gradcam_data:payload.ecgGradcamData,raw_ecg:payload.rawEcg}),
    });
    return {predictionId:raw.prediction_id,riskScore:raw.risk_score ?? 0,shapData:raw.shap_data,failureAnalysisText:raw.failure_analysis_text,pdfStoragePath:raw.pdf_storage_path,pdfSignedUrl:raw.pdf_signed_url};
  }

  async getHistory(limit: number = 20, offset: number = 0): Promise<HistoryResponse> {
    const raw = await this.request<{items:Array<{prediction_id:string;created_at:string;risk_score:number;streams_used:string[];has_report:boolean}>;total:number}>(`/api/v1/history?limit=${limit}&offset=${offset}`, {
      method: 'GET',
    });
    return {total:raw.total,items:raw.items.map(item=>({predictionId:item.prediction_id,createdAt:item.created_at,riskScore:item.risk_score,streamsUsed:item.streams_used,hasReport:item.has_report}))};
  }

  // PLATFORM EXTENSION ENDPOINTS

  async onboardProfile(data: ProfileInput): Promise<Profile> {
    const raw = await this.request<RawProfile>('/api/v1/profiles/onboard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mapProfileInput(data)),
    });
    return mapProfile(raw);
  }

  async getMyProfile(): Promise<Profile> {
    return mapProfile(await this.request<RawProfile>('/api/v1/profiles/me', {
      method: 'GET',
    }));
  }

  async runClinicalInference(payload: PredictRequest): Promise<PredictResponse> {
    const raw = await this.request<RawPrediction>('/api/v1/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mapPredictRequest(payload)),
    });
    return mapPredictionResponse(raw);
  }

  async getClinicalAnalytics(): Promise<ClinicalAnalytics> {
    const raw = await this.request<Record<string, unknown>>('/api/v1/clinical/analytics', {
      method: 'GET',
    });
    return {
      trends:(raw.trends as Array<{created_at:string;risk_score:number}>|undefined)?.map(item=>({createdAt:item.created_at,riskScore:item.risk_score})),
      averageRiskAll:raw.average_risk_all as number|undefined,
      totalPatients:raw.total_patients as number|undefined,
      highRiskPatients:raw.high_risk_patients as number|undefined,
      riskDistribution: raw.risk_distribution as {low: number, medium: number, high: number} | undefined,
      topPatients: (raw.top_patients as any[])?.map(item => ({
        patientId: item.patient_id,
        name: item.name,
        email: item.email,
        riskScore: item.risk_score,
        lastAssessment: item.last_assessment
      }))
    };
  }

  async getMyReports(): Promise<StoredPrediction[]> {
    const raw = await this.request<RawStoredPrediction[]>('/api/v1/reports/mine', {
      method: 'GET',
    });
    return raw.map(mapStoredPrediction);
  }

  async ensureReport(predictionId: string): Promise<{ downloadUrl: string; generated: boolean }> {
    const raw = await this.request<{ download_url: string; generated: boolean }>(`/api/v1/reports/${predictionId}/ensure`, { method: 'POST' });
    return {downloadUrl:raw.download_url,generated:raw.generated};
  }

  async getPatients(): Promise<DoctorPatientLink[]> {
    const raw = await this.request<RawLink[]>('/api/v1/clinical/patients', {
      method: 'GET',
    });
    return raw.map(item=>({id:item.id,patientId:item.patient_id,doctorId:item.doctor_id,status:item.status,createdAt:item.created_at,profiles:mapProfile(item.profiles),latest_triage_tier:item.latest_triage_tier}));
  }

  async requestLink(doctorId: string): Promise<unknown> {
    return this.request<unknown>(`/api/v1/clinical/link?doctor_id=${doctorId}`, {
      method: 'POST',
    });
  }

  async updateLinkStatus(linkId: string, status: 'accepted' | 'rejected'): Promise<unknown> {
    return this.request<unknown>(`/api/v1/clinical/link/${linkId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
  }

  async getDoctorCode(): Promise<{ code: string }> {
    return this.request<{ code: string }>('/api/v1/clinical/doctor-code', { method: 'GET' });
  }

  async connectByDoctorCode(code: string): Promise<DoctorConnection> {
    const raw = await this.request<{message:string;doctor:RawProfile}>(`/api/v1/clinical/connect-by-code?code=${encodeURIComponent(code)}`, { method: 'POST' });
    return {message:raw.message,doctor:mapProfile(raw.doctor) as DoctorConnection['doctor']};
  }

  async getPatientRecord(patientId: string): Promise<PatientRecord> {
    const raw = await this.request<{profile:RawProfile;predictions:RawStoredPrediction[]}>(`/api/v1/clinical/patients/${patientId}/record`, { method: 'GET' });
    return {profile:mapProfile(raw.profile),predictions:raw.predictions.map(mapStoredPrediction)};
  }

  async addDoctorNote(predictionId: string, note: string, priority: string = 'normal'): Promise<unknown> {
    return this.request<unknown>(`/api/v1/clinical/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prediction_id: predictionId, note, priority }),
    });
  }

  async addPrescription(patientId: string, medicationName: string, dosage: string, frequency: string, duration: string, notes: string = ''): Promise<unknown> {
    return this.request<unknown>(`/api/v1/clinical/patients/${patientId}/prescriptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ medication_name: medicationName, dosage, frequency, duration, notes }),
    });
  }

  async getChatMessages(otherUserId: string): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/api/v1/chat/messages/${otherUserId}`, { method: 'GET' });
  }

  async sendChatMessage(otherUserId: string, content: string): Promise<ChatMessage> {
    return this.request<ChatMessage>(`/api/v1/chat/messages/${otherUserId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
  }

  async getPatientForecast(patientId: string): Promise<ForecastResponse> {
    return this.request<ForecastResponse>(`/api/v1/clinical/patients/${patientId}/forecast`, { method: 'GET' });
  }

  async getNotifications(unreadOnly = false): Promise<PaginatedNotifications> {
    const raw = await this.request<any>(`/api/v1/clinical/notifications?unread_only=${unreadOnly}`, { method: 'GET' });
    return {
      items: raw.items.map((n: any) => ({
        id: n.id, userId: n.user_id, title: n.title, message: n.message,
        type: n.type, read: n.read, createdAt: n.created_at
      })),
      total: raw.total,
      unreadCount: raw.unread_count
    };
  }

  async markNotificationRead(id: string): Promise<void> {
    await this.request(`/api/v1/clinical/notifications/${id}/read`, { method: 'PATCH' });
  }

  async markAllNotificationsRead(): Promise<void> {
    await this.request('/api/v1/clinical/notifications/read-all', { method: 'PATCH' });
  }
}

export const api = new ApiClient();
