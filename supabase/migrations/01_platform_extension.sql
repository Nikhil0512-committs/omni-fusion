-- ==============================================================================
-- OMNI-FUSION PLATFORM EXTENSION MIGRATION
-- ==============================================================================

-- 1. PROFILES
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('PATIENT', 'DOCTOR')),
    full_name TEXT,
    email TEXT,
    date_of_birth DATE,
    age INTEGER,
    sex TEXT,
    height_cm FLOAT,
    weight_kg FLOAT,
    bmi FLOAT,
    smoking_status TEXT,
    alcohol_use TEXT,
    exercise_frequency TEXT,
    family_history JSONB,
    diagnoses JSONB,
    medications JSONB,
    medical_registration_number TEXT,
    specialization TEXT,
    hospital TEXT,
    phone TEXT,
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. EXTEND PREDICTIONS
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS patient_id UUID REFERENCES profiles(id) ON DELETE CASCADE;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS doctor_id UUID REFERENCES profiles(id) ON DELETE SET NULL;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS doctor_reviewed BOOLEAN DEFAULT FALSE;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS doctor_note TEXT;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITH TIME ZONE;

-- 3. DOCTOR_PATIENT_LINKS
CREATE TABLE IF NOT EXISTS doctor_patient_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(doctor_id, patient_id)
);

-- 4. DOCTOR_NOTES
CREATE TABLE IF NOT EXISTS doctor_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('normal', 'follow-up', 'urgent')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. NOTIFICATIONS
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==============================================================================
-- RLS POLICIES
-- ==============================================================================

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctor_patient_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctor_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Service Role full access
CREATE POLICY "Service Role Full Access profiles" ON profiles FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service Role Full Access doctor_patient_links" ON doctor_patient_links FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service Role Full Access doctor_notes" ON doctor_notes FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');
CREATE POLICY "Service Role Full Access notifications" ON notifications FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Profiles RLS
-- Users can read their own profile
CREATE POLICY "Users can read own profile" ON profiles FOR SELECT USING (auth.uid() = id);
-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
-- Doctors can read profiles of patients they are linked to (accepted)
CREATE POLICY "Doctors can read linked patients" ON profiles FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM doctor_patient_links 
        WHERE doctor_id = auth.uid() AND patient_id = profiles.id AND status = 'accepted'
    )
);
-- Patients can read profiles of doctors
CREATE POLICY "Patients can read doctor profiles" ON profiles FOR SELECT USING (
    role = 'DOCTOR'
);

-- Doctor Patient Links RLS
CREATE POLICY "Users can view their links" ON doctor_patient_links FOR SELECT USING (
    auth.uid() = doctor_id OR auth.uid() = patient_id
);
CREATE POLICY "Users can insert links" ON doctor_patient_links FOR INSERT WITH CHECK (
    auth.uid() = doctor_id OR auth.uid() = patient_id
);
CREATE POLICY "Users can update their links" ON doctor_patient_links FOR UPDATE USING (
    auth.uid() = doctor_id OR auth.uid() = patient_id
);

-- Predictions RLS (Extending existing)
-- Patients can view their own predictions
CREATE POLICY "Patients can view own predictions" ON predictions FOR SELECT USING (
    auth.uid() = patient_id
);
-- Doctors can view predictions of their accepted patients
CREATE POLICY "Doctors can view linked patient predictions" ON predictions FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM doctor_patient_links 
        WHERE doctor_id = auth.uid() AND patient_id = predictions.patient_id AND status = 'accepted'
    )
);

-- Doctor Notes RLS
CREATE POLICY "Users can view relevant notes" ON doctor_notes FOR SELECT USING (
    auth.uid() = doctor_id OR 
    EXISTS (
        SELECT 1 FROM predictions WHERE id = doctor_notes.prediction_id AND patient_id = auth.uid()
    )
);

-- Notifications RLS
CREATE POLICY "Users can view own notifications" ON notifications FOR SELECT USING (
    auth.uid() = user_id
);
CREATE POLICY "Users can update own notifications" ON notifications FOR UPDATE USING (
    auth.uid() = user_id
);

-- Reports RLS (Extending existing)
-- Patients can view reports for their own predictions
CREATE POLICY "Patients can view own reports" ON reports FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM predictions WHERE id = reports.prediction_id AND patient_id = auth.uid()
    )
);
-- Doctors can view reports of their accepted patients
CREATE POLICY "Doctors can view linked patient reports" ON reports FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM predictions p
        JOIN doctor_patient_links l ON p.patient_id = l.patient_id
        WHERE p.id = reports.prediction_id AND l.doctor_id = auth.uid() AND l.status = 'accepted'
    )
);
