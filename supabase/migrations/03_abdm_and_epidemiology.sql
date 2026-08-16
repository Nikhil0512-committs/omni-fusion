-- ==============================================================================
-- ABDM & EPIDEMIOLOGY EXTENSION MIGRATION
-- ==============================================================================

-- 1. ADD FIELDS TO PROFILES FOR HEATMAP
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS pincode TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS district TEXT;

-- 2. ADD OFFLINE SYNC ID TO PREDICTIONS FOR DEDUPLICATION
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS offline_sync_id UUID UNIQUE;

-- 3. CREATE ABDM CONSENTS TABLE
CREATE TABLE IF NOT EXISTS abdm_consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    purpose TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('granted', 'revoked', 'expired')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- RLS POLICIES
-- ==============================================================================

ALTER TABLE abdm_consents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service Role Full Access abdm_consents" ON abdm_consents FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Patients can view their own consents
CREATE POLICY "Patients can view own consents" ON abdm_consents FOR SELECT USING (
    auth.uid() = patient_id
);

-- Patients can update their own consents
CREATE POLICY "Patients can update own consents" ON abdm_consents FOR UPDATE USING (
    auth.uid() = patient_id
);

-- Patients can insert their own consents
CREATE POLICY "Patients can insert own consents" ON abdm_consents FOR INSERT WITH CHECK (
    auth.uid() = patient_id
);
