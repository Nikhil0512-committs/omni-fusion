# Omni-Fusion

**Omni-Fusion** is an advanced, multimodal AI diagnostic platform designed to predict cardiovascular risk by fusing multiple data modalities:
1. **12-Lead ECG Waveforms** (Processed via 1D ResNet)
2. **Clinical Vitals/Demographics** (Processed via PyTorch MLP)
3. **Historical Patient Records** (Optional, processed via PyTorch GRU)

The platform features an algorithmic equity constraint to ensure equal predictive performance across demographic groups, and provides complete explainability using SHAP (for tabular data) and Grad-CAM (for raw ECG waveforms).

## Data & Model Attribution

This project's models were trained using two publicly available PhysioNet datasets:

- **PTB-XL** — a large publicly available electrocardiography dataset, licensed under
  [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/). Used here to train the
  ECG diagnostic-pattern branch of the model.
- **MIMIC-IV Clinical Database Demo** — a deidentified subset of ICU/hospital admission
  data, provided under PhysioNet's Health Data License. Used here to train the vitals
  and historical-data branches of the model.

Please refer to each dataset's original documentation and license terms on
[PhysioNet](https://physionet.org/) before reusing or extending this project with
your own data.

**This project is a research/demonstration prototype and is not intended for clinical
use, diagnosis, or treatment decisions.** Model outputs are trained on deidentified,
limited-scope data and have not been clinically validated.

## System Architecture
- **AI Model**: OmniFusionNet (PyTorch). Uses dynamic routing to function correctly even if the historical patient records are missing.
- **Backend API**: FastAPI (Python 3.13) offering strict Pydantic v2 schemas, REST endpoints for inference and historical data ingestion.
- **Frontend Dashboard**: Next.js 16 App Router (TypeScript, React) with D3.js and Recharts for complex data visualization.
- **Persistence**: Supabase (PostgreSQL, Storage). Uses Service Role for secure backend-only operations (predictions, reports, upload sessions).
- **Explainability**: Captum LayerGradCam (ECG heatmaps) and SHAP KernelExplainer (tabular feature importance).

## Cold-Start Deployment Guide

### Prerequisites
- Docker & Docker Compose
- Node.js 22.x
- Python 3.13
- A Supabase Project (Cloud or Local)

### 1. Database Setup (Supabase)
1. Create a new Supabase project.
2. Navigate to the SQL Editor in your Supabase dashboard.
3. Execute the contents of `supabase/schema.sql` to create the necessary tables (`upload_sessions`, `predictions`, `reports`) and RLS policies.
4. Navigate to Storage and create a public bucket named `reports`.

### 2. Environment Configuration
#### Backend
1. Copy `backend/.env.example` to `backend/.env`.
2. Fill in the values for `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (Found in Supabase Settings -> API).
   *Note: Never use the `anon` key on the backend for this project, it strictly relies on the Service Role key to bypass RLS.*
3. Ensure `MODEL_PATH` points to the `omni_fusion_final.pt` checkpoint (e.g., `../models/exported/omni_fusion_final.pt`).
4. Ensure the following model artifacts are present in your workspace before starting the backend (run the training/preprocessing scripts if missing):
   - `models/exported/omni_fusion_final.pt` (Final trained model checkpoint)
   - `models/checkpoints/vitals_scaler.pkl`
   - `models/checkpoints/vitals_scaler_feature_order.pkl`
   - `models/checkpoints/historical_knn_imputer.pkl`
   - `models/checkpoints/shap_background.npy`
   - `models/checkpoints/ecg_branch_config.json`
   - `models/checkpoints/vitals_branch_config.json`
   - `models/checkpoints/historical_branch_config.json`

#### Frontend
1. Copy `frontend/.env.local.example` to `frontend/.env.local`.
2. Ensure `NEXT_PUBLIC_API_BASE_URL` is set to `http://localhost:8000` (or wherever your FastAPI backend is running).

### 3. Running Locally (Docker Compose)
The easiest way to start both the backend and frontend is using Docker Compose:
```bash
docker-compose up --build
```
This will start:
- **Backend (FastAPI)** on port `8000`
- **Frontend (Next.js)** on port `3000`

### 4. Running Locally (Manual)
#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### 5. Accessing the Application
Once both servers are running, open your browser and navigate to:
**http://localhost:3000**

## Project Structure
- `backend/`: FastAPI backend and PyTorch inference logic.
- `frontend/`: Next.js frontend code.
- `supabase/`: Database schema and migration files.
- `models/`: Model checkpoints and configs.
- `training_scripts/`: Scripts used for data ingestion, preprocessing, and training the model branches (Phases 1-7).
- `docs/`: Progress logs and system documentation.

## Testing
Run the backend test suite using `pytest`:
```bash
cd backend
PYTHONPATH=. pytest tests/
```

To run end-to-end tests using Puppeteer (assuming both servers are running):
```bash
bash scripts/run_e2e.sh
```

## Contributing

Backend documentation uses Google-style docstrings. Keep API wire fields in
snake_case and map them to camelCase only at the frontend API boundary.

## Generated artifacts

Training logs under `logs/` and explainability exports under `xai_outputs/`
are generated by `training_scripts/03_train_ecg_branch.py` through
`training_scripts/07_xai_analysis.py` and are intentionally not versioned.
The small validated runtime checkpoint at
`models/exported/omni_fusion_final.pt` remains versioned so a fresh clone can
run inference without retraining; Git LFS is not available in the validated
environment. Manual utilities live under `scripts/`.

## Submission Deliverables (Phase 21)
- **Kaggle Manuscript**: `OmniFusion_Report.md` details the technical architecture and the multimodal ablation study.
- **SIH Pitch Deck**: `OmniFusion_Pitch.md` outlines the 10-slide structure and live demo runbook.
- **Compliance**: `SECURITY.md` documents FHIR R4 mapping, simulated ABDM integrations, and RLS security practices.
- **Ablation Study**: `training_scripts/09_ablation_study.py` demonstrates the resilience of the late-fusion routing mechanism.

## License

See [LICENSE](./LICENSE) for details (MIT).
