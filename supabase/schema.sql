-- ==============================================================================
-- KAIRO — Metric-Aware Blueprint Intelligence
-- Supabase Database Schema & Storage Setup
-- ==============================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Create Reconstructions Table
CREATE TABLE IF NOT EXISTS public.reconstructions (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    name TEXT NOT NULL DEFAULT 'Untitled Blueprint',
    status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
    thumbnail_url TEXT,
    model_url TEXT,
    json_url TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ DEFAULT timezone('utc'::text, now())
);

-- 3. Create Indexes for High Performance
CREATE INDEX IF NOT EXISTS idx_reconstructions_user_id ON public.reconstructions(user_id);
CREATE INDEX IF NOT EXISTS idx_reconstructions_created_at ON public.reconstructions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reconstructions_status ON public.reconstructions(status);

-- 4. Enable Row Level Security (RLS)
ALTER TABLE public.reconstructions ENABLE ROW LEVEL SECURITY;

-- 5. RLS Policies
-- Allow anyone to read reconstructions if public, or their own if authenticated
CREATE POLICY "Users can read own reconstructions or public reconstructions"
    ON public.reconstructions
    FOR SELECT
    USING (
        auth.uid() IS NULL 
        OR user_id IS NULL 
        OR auth.uid() = user_id
    );

-- Allow authenticated users or anonymous demos to insert reconstructions
CREATE POLICY "Users can insert reconstructions"
    ON public.reconstructions
    FOR INSERT
    WITH CHECK (
        auth.uid() IS NULL 
        OR auth.uid() = user_id 
        OR user_id IS NULL
    );

-- Allow users to update their own reconstructions
CREATE POLICY "Users can update own reconstructions"
    ON public.reconstructions
    FOR UPDATE
    USING (
        auth.uid() IS NULL 
        OR auth.uid() = user_id 
        OR user_id IS NULL
    );

-- 6. Setup Supabase Storage Buckets
-- Run this in the Supabase Storage settings or via SQL:
INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('blueprints', 'blueprints', true),
    ('models', 'models', true)
ON CONFLICT (id) DO UPDATE SET public = true;

-- Storage RLS Policies: Allow public download of blueprint images and 3D models
CREATE POLICY "Public Blueprint Access"
    ON storage.objects FOR SELECT
    USING (bucket_id IN ('blueprints', 'models'));

CREATE POLICY "Authenticated Users Blueprint Upload"
    ON storage.objects FOR INSERT
    WITH CHECK (bucket_id IN ('blueprints', 'models'));
