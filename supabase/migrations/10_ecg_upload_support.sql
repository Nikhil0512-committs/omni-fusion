-- ==============================================================================
-- OMNI-FUSION MIGRATION: ECG UPLOAD SUPPORT
-- ==============================================================================

-- 1. Alter predictions table to allow NULL risk_score
ALTER TABLE predictions ALTER COLUMN risk_score DROP NOT NULL;

-- 2. Add new columns for image storage and ECG abnormality
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS uploaded_image_path TEXT;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS ecg_abnormality TEXT;
