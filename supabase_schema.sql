-- Run this in Supabase SQL Editor to create the holdings table
-- Supabase Dashboard > SQL Editor > New Query > paste this > Run

CREATE TABLE holdings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticker TEXT NOT NULL,
    company_name TEXT,
    shares NUMERIC NOT NULL CHECK (shares > 0),
    currency TEXT NOT NULL DEFAULT 'USD',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups by ticker
CREATE INDEX idx_holdings_ticker ON holdings (ticker);

-- Auto-update the updated_at timestamp on changes
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER holdings_updated_at
    BEFORE UPDATE ON holdings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Enable Row Level Security (required by Supabase)
ALTER TABLE holdings ENABLE ROW LEVEL SECURITY;

-- Allow all operations via the anon/service key (single-user app)
CREATE POLICY "Allow all operations" ON holdings
    FOR ALL
    USING (true)
    WITH CHECK (true);
