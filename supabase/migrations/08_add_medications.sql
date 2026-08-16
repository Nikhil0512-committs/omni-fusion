ALTER TABLE public.profiles
ADD COLUMN IF NOT EXISTS medications JSONB DEFAULT '[]'::jsonb;
