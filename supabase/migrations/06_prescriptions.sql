-- ==============================================================================
-- 06 PRESCRIPTIONS
-- ==============================================================================

CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    medication_name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    frequency TEXT NOT NULL,
    duration TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE prescriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service Role Full Access prescriptions" ON prescriptions FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Doctors can create prescriptions for patients they are connected to
CREATE POLICY "Doctors can create prescriptions" ON prescriptions FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM doctor_patient_links 
        WHERE doctor_id = auth.uid() AND patient_id = prescriptions.patient_id AND status = 'accepted'
    )
);

-- Doctors can view prescriptions of patients they are connected to
CREATE POLICY "Doctors can view prescriptions" ON prescriptions FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM doctor_patient_links 
        WHERE doctor_id = auth.uid() AND patient_id = prescriptions.patient_id AND status = 'accepted'
    )
);

-- Patients can view their own prescriptions
CREATE POLICY "Patients can view own prescriptions" ON prescriptions FOR SELECT USING (
    auth.uid() = patient_id
);
