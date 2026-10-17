-- 管線表不歸 Alembic；既有案例保留在練習池，可重複執行。
ALTER TABLE game_cases ADD COLUMN IF NOT EXISTS pool text NOT NULL DEFAULT 'practice';
ALTER TABLE game_cases ADD COLUMN IF NOT EXISTS pattern_key text;
CREATE INDEX IF NOT EXISTS game_cases_pool_published_idx ON game_cases (pool, fraud_type, is_scam) WHERE status = 'published';
