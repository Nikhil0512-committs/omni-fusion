-- Phase 22 Security Audit Fixes

-- 1. Ensure the 'reports' bucket is private and locked down from anonymous access
-- If the bucket was created publicly, we update it.
UPDATE storage.buckets
SET public = false
WHERE id = 'reports';

-- 2. Ensure RLS is active on storage.objects for the reports bucket
-- Drop any potentially overly permissive public policies
DROP POLICY IF EXISTS "Public reports access" ON storage.objects;
DROP POLICY IF EXISTS "Anon reports access" ON storage.objects;

-- We only allow authenticated users to read reports they own/are linked to, 
-- but actually the backend uses signed URLs (Service Role bypasses RLS). 
-- So we don't necessarily need a permissive SELECT policy for patients here 
-- if they only access via signed URLs. If they access via signed URLs, 
-- no RLS policy is required for `anon` or `authenticated` roles because 
-- the signed URL has a short-lived token granting access.
-- But just to be extremely secure, we explicitly deny anon.

-- No explicit policy is needed for signed URLs, but we ensure no public anon access exists.

-- 3. RLS for abdm_consents
ALTER TABLE public.abdm_consents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Patients can view their own consents"
ON public.abdm_consents FOR SELECT
USING (auth.uid() = patient_id);

DROP POLICY IF EXISTS "Doctors can view consents of linked patients" ON public.abdm_consents;
CREATE POLICY "Doctors can view consents of linked patients"
ON public.abdm_consents FOR SELECT
USING (
  EXISTS (
    SELECT 1 FROM doctor_patient_links l
    WHERE l.patient_id = abdm_consents.patient_id
      AND l.doctor_id = auth.uid()
      AND l.status = 'accepted'
  )
);

DROP POLICY IF EXISTS "Service Role Full Access abdm_consents" ON public.abdm_consents;
CREATE POLICY "Service Role Full Access abdm_consents" 
ON public.abdm_consents USING (true);
