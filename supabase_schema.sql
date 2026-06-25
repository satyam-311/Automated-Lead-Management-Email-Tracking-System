-- ─────────────────────────────────────────────────────────────────────────────
--  LeadFlow — Supabase / PostgreSQL Schema
--
--  Run this in the Supabase SQL Editor to create the leads table.
--  After running, copy the connection string from:
--  Supabase Dashboard → Settings → Database → Connection String
--  and set DATABASE_URL in your .env file (see .env.example).
-- ─────────────────────────────────────────────────────────────────────────────

-- Main leads table
CREATE TABLE IF NOT EXISTS leads (
    id            SERIAL          PRIMARY KEY,
    name          TEXT            NOT NULL,
    email         TEXT            NOT NULL,
    phone         TEXT            NOT NULL,
    company       TEXT,
    requirement   TEXT,
    submitted_at  TIMESTAMPTZ     DEFAULT NOW(),
    email_sent    INTEGER         DEFAULT 0,
    email_opened  INTEGER         DEFAULT 0,
    link_clicked  INTEGER         DEFAULT 0,
    category      TEXT            DEFAULT 'General Inquiry',
    priority      TEXT            DEFAULT 'Medium',
    confidence    INTEGER         DEFAULT 0
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_leads_submitted_at ON leads (submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_category     ON leads (category);
CREATE INDEX IF NOT EXISTS idx_leads_priority     ON leads (priority);
CREATE INDEX IF NOT EXISTS idx_leads_email        ON leads (email);

-- ─────────────────────────────────────────────────────────────────────────────
--  HOW TO SWITCH FROM SQLITE TO SUPABASE
-- ─────────────────────────────────────────────────────────────────────────────
--
--  1. Run this SQL in the Supabase SQL Editor.
--
--  2. Install the PostgreSQL driver:
--       pip install psycopg2-binary
--     Add psycopg2-binary to requirements.txt as well.
--
--  3. Add to your .env:
--       DATABASE_URL=postgresql://postgres:<password>@db.<ref>.supabase.co:5432/postgres
--
--  4. In database.py, swap _connect() for the Postgres version:
--
--       import psycopg2
--       import psycopg2.extras
--
--       def _connect():
--           conn = psycopg2.connect(
--               os.getenv("DATABASE_URL"),
--               cursor_factory=psycopg2.extras.RealDictCursor
--           )
--           return conn
--
--  5. Change every parameterised placeholder from ? to %s
--     (psycopg2 uses %s, not ? like sqlite3).
--
--  6. On Render, add DATABASE_URL as an environment variable in the dashboard.
--
--  Alternative: use Render's own free PostgreSQL instance.
--  Render Dashboard → New → PostgreSQL → copy the Internal Database URL.
-- ─────────────────────────────────────────────────────────────────────────────
