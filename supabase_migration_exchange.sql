-- Migration for existing Supabase databases.
-- Adds the exchange column used to store the exact Yahoo listing selected by the user.

ALTER TABLE holdings
ADD COLUMN IF NOT EXISTS exchange TEXT;
