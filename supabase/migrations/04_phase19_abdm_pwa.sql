-- ==============================================================================
-- OMNI-FUSION PHASE 19 MIGRATION: ABDM & PWA
-- ==============================================================================

-- 1. Extend profiles for Epidemiological Dashboard
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS district TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS pincode TEXT;

-- 2. Create abdm_consents table
CREATE TABLE IF NOT EXISTS abdm_consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    purpose TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'revoked', 'expired')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_abdm_consents_patient_id ON abdm_consents(patient_id);

-- 3. RLS for abdm_consents
ALTER TABLE abdm_consents ENABLE ROW LEVEL SECURITY;

-- Service Role full access
DROP POLICY IF EXISTS "Service Role Full Access abdm_consents" ON abdm_consents;
CREATE POLICY "Service Role Full Access abdm_consents" ON abdm_consents FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Patients can view and manage their own consents
DROP POLICY IF EXISTS "Patients can view own consents" ON abdm_consents;
CREATE POLICY "Patients can view own consents" ON abdm_consents FOR SELECT USING (
    auth.uid() = patient_id
);
DROP POLICY IF EXISTS "Patients can insert own consents" ON abdm_consents;
CREATE POLICY "Patients can insert own consents" ON abdm_consents FOR INSERT WITH CHECK (
    auth.uid() = patient_id
);
DROP POLICY IF EXISTS "Patients can update own consents" ON abdm_consents;
CREATE POLICY "Patients can update own consents" ON abdm_consents FOR UPDATE USING (
    auth.uid() = patient_id
);
