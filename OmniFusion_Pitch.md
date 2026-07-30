# Omni-Fusion Pitch Deck (SIH Submission)

## Slide 1: Title Slide
**Title:** Omni-Fusion: Multimodal Cardiovascular AI
**Subtitle:** Bridging the gap in clinical decision support with equitable, resilient, and explainable deep learning.
**Visual:** Omni-Fusion logo and high-level abstract diagram.

## Slide 2: The Problem
**Title:** The Cardiovascular Crisis in High-Volume Settings
- **Fragmented Data:** Vitals, EHR histories, and ECGs live in silos.
- **Resource Constraints:** In low-resource settings, patient data is often missing (e.g., no historical EHR).
- **Algorithmic Bias:** Existing models often perform worse on underrepresented demographics (e.g., women).

## Slide 3: The Solution
**Title:** A Unified Multimodal Approach
- We fuse three distinct data streams using late-fusion neural network architectures:
  1. Real-time 12-lead ECGs (1D ResNet)
  2. Immediate Vitals (Deep MLP)
  3. Longitudinal History (GRU)

## Slide 4: Key Innovation 1 - Resilience
**Title:** Dynamic Routing & Missing Modality Support
- What happens when a patient has no historical data? Our network uses **Dynamic Routing via Masking** during training.
- Result: The model seamlessly falls back to available streams (ECG + Vitals) without failing, ensuring 100% uptime in low-resource environments.

## Slide 5: Key Innovation 2 - Algorithmic Equity
**Title:** Closing the Demographic Gap
- Traditional models had a 12.5% divergence in accuracy between men and women.
- We introduced a custom **Equity-Aware Loss Function**: penalizing the network during training if error rates diverge between subgroups.
- Result: Divergence reduced to under 1.5%.

## Slide 6: Key Innovation 3 - Trust & Explainability
**Title:** Explainable AI (XAI)
- Doctors need to trust the AI. Omni-Fusion provides:
  - **1D Grad-CAM:** Thermal heatmaps directly on the ECG waveforms highlighting anomalies (e.g., T-wave inversions).
  - **SHAP Analysis:** Waterfall charts showing exactly how much each vital sign (e.g., Troponin, Heart Rate) contributed to the final risk score.

## Slide 7: Technical Architecture
**Title:** Secure & Scalable Architecture
- **Frontend:** Next.js + TailwindCSS + Recharts for responsive, interactive visualization.
- **Backend:** FastAPI + PyTorch serving low-latency multimodal inference.
- **Data & Auth:** Supabase (PostgreSQL) with strict Role-Based Access Control (RLS) for patient-doctor linking.

## Slide 8: Compliance & Interoperability
**Title:** Built for National Health Infrastructure
- **FHIR R4:** Clinical reports mapped to standard FHIR schemas for interoperability.
- **ABDM Readiness:** Modeled to integrate seamlessly with the Ayushman Bharat Digital Mission (consent workflows & ABHA IDs).

## Slide 9: Impact
**Title:** What this means for patients
- Faster triage in emergency rooms.
- Reduced physician burnout through automated risk stratification.
- Equitable healthcare outcomes regardless of demographic background.

## Slide 10: Live Demo Runbook
**Title:** Omni-Fusion in Action
1. Log in as a Patient.
2. Upload a sample historical CSV (or let the system fall back to ECG).
3. Execute Multimodal Inference.
4. Explore the SHAP Waterfall and ECG Heatmaps.
5. Generate the final Clinical PDF Report and securely share it with the linked Doctor.
