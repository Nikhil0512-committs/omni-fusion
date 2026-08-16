-- ==============================================================================
-- OMNI-FUSION DATABASE SCHEMA
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. UPLOAD SESSIONS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS upload_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_filename TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    imputation_summary JSONB,
    status TEXT NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. PREDICTIONS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    upload_session_id UUID REFERENCES upload_sessions(id) ON DELETE CASCADE,
    risk_score FLOAT NOT NULL,
    streams_used JSONB NOT NULL,
    raw_input_ref JSONB
);

CREATE INDEX IF NOT EXISTS idx_predictions_upload_session_id ON predictions(upload_session_id);

-- ------------------------------------------------------------------------------
-- 3. REPORTS
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    shap_data JSONB,
    gradcam_ref TEXT,
    failure_analysis_text TEXT,
    pdf_storage_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_reports_prediction_id ON reports(prediction_id);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================
-- We explicitly enable RLS on all tables.
ALTER TABLE upload_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;

-- Policy: Restrict all access strictly to the `service_role` (Backend).
-- Since the frontend will not communicate directly with Supabase, the anon role 
-- has no permissions. Only the backend using the SERVICE_ROLE_KEY can read/write.
CREATE POLICY "Service Role Full Access upload_sessions" ON upload_sessions
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service Role Full Access predictions" ON predictions
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service Role Full Access reports" ON reports
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
