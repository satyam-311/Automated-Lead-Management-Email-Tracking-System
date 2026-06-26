import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Backend detection ─────────────────────────────────────────────────────────
# If DATABASE_URL is set → PostgreSQL (Supabase / Render PG)
# Otherwise             → SQLite (local development)
_DATABASE_URL = os.getenv("DATABASE_URL")
_USE_PG = bool(_DATABASE_URL)

if _USE_PG:
    import psycopg2
    import psycopg2.extras
    _PH = "%s"
else:
    import sqlite3
    _DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")
    _PH = "?"


def _connect():
    if _USE_PG:
        return psycopg2.connect(
            _DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _q(sql: str) -> str:
    """Swap ? → %s for PostgreSQL."""
    return sql.replace("?", _PH)


def init_db():
    conn = _connect()
    try:
        c = conn.cursor()
        if _USE_PG:
            c.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id            SERIAL          PRIMARY KEY,
                    name          TEXT            NOT NULL,
                    email         TEXT            NOT NULL,
                    phone         TEXT            NOT NULL,
                    company       TEXT,
                    requirement   TEXT,
                    submitted_at  TEXT,
                    email_sent    INTEGER         DEFAULT 0,
                    email_opened  INTEGER         DEFAULT 0,
                    link_clicked  INTEGER         DEFAULT 0,
                    category      TEXT            DEFAULT 'General Inquiry',
                    priority      TEXT            DEFAULT 'Medium',
                    confidence    INTEGER         DEFAULT 0
                )
            """)
        else:
            c.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    name          TEXT    NOT NULL,
                    email         TEXT    NOT NULL,
                    phone         TEXT    NOT NULL,
                    company       TEXT,
                    requirement   TEXT,
                    submitted_at  TEXT,
                    email_sent    INTEGER DEFAULT 0,
                    email_opened  INTEGER DEFAULT 0,
                    link_clicked  INTEGER DEFAULT 0,
                    category      TEXT    DEFAULT 'General Inquiry',
                    priority      TEXT    DEFAULT 'Medium',
                    confidence    INTEGER DEFAULT 0
                )
            """)
            # Non-destructive column migrations for older schemas
            for col, defn in [
                ("category",   "TEXT DEFAULT 'General Inquiry'"),
                ("priority",   "TEXT DEFAULT 'Medium'"),
                ("confidence", "INTEGER DEFAULT 0"),
            ]:
                try:
                    c.execute(f"ALTER TABLE leads ADD COLUMN {col} {defn}")
                except sqlite3.OperationalError:
                    pass  # column already exists
        conn.commit()
        logger.info("Database ready (backend=%s)", "PostgreSQL" if _USE_PG else "SQLite")
    finally:
        conn.close()


def insert_lead(name, email, phone, company, requirement,
                category="General Inquiry", priority="Medium", confidence=0):
    conn = _connect()
    try:
        c = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if _USE_PG:
            c.execute(
                "INSERT INTO leads "
                "(name,email,phone,company,requirement,submitted_at,category,priority,confidence) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (name, email, phone, company, requirement, now, category, priority, confidence),
            )
            lead_id = c.fetchone()["id"]
        else:
            c.execute(
                "INSERT INTO leads "
                "(name,email,phone,company,requirement,submitted_at,category,priority,confidence) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (name, email, phone, company, requirement, now, category, priority, confidence),
            )
            lead_id = c.lastrowid
        conn.commit()
        logger.info("Lead inserted: id=%s category=%s priority=%s", lead_id, category, priority)
        return lead_id
    finally:
        conn.close()


def _update(sql: str, params: tuple) -> bool:
    conn = _connect()
    try:
        c = conn.cursor()
        c.execute(_q(sql), params)
        affected = c.rowcount
        conn.commit()
        if affected == 0:
            logger.warning("_update matched 0 rows: sql=%r params=%r", sql, params)
        return affected > 0
    finally:
        conn.close()


def mark_email_sent(lead_id) -> bool:
    ok = _update("UPDATE leads SET email_sent=1 WHERE id=?", (lead_id,))
    if ok:
        logger.info("email_sent marked: lead_id=%s", lead_id)
    else:
        logger.error("mark_email_sent updated 0 rows for lead_id=%s", lead_id)
    return ok


def mark_email_opened(lead_id) -> bool:
    ok = _update("UPDATE leads SET email_opened=1 WHERE id=?", (lead_id,))
    logger.info("Email opened: lead_id=%s rows_affected=%s", lead_id, ok)
    return ok


def mark_link_clicked(lead_id) -> bool:
    ok = _update("UPDATE leads SET link_clicked=1 WHERE id=?", (lead_id,))
    logger.info("Link clicked: lead_id=%s rows_affected=%s", lead_id, ok)
    return ok


def get_all_leads():
    conn = _connect()
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM leads ORDER BY submitted_at DESC")
        return [dict(r) for r in c.fetchall()]
    finally:
        conn.close()


def get_stats():
    conn = _connect()
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) AS n FROM leads")
        total = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM leads WHERE email_sent=1")
        sent = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM leads WHERE email_opened=1")
        opened = c.fetchone()["n"]
        c.execute("SELECT COUNT(*) AS n FROM leads WHERE link_clicked=1")
        clicked = c.fetchone()["n"]
        return {"total": total, "sent": sent, "opened": opened, "clicked": clicked}
    finally:
        conn.close()
