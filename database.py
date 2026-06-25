import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = "leads.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    try:
        conn.execute('''
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
                category      TEXT    DEFAULT "General Inquiry",
                priority      TEXT    DEFAULT "Medium",
                confidence    INTEGER DEFAULT 0
            )
        ''')
        # Non-destructive migration: add columns added after initial release
        for col, definition in [
            ("category",   'TEXT DEFAULT "General Inquiry"'),
            ("priority",   'TEXT DEFAULT "Medium"'),
            ("confidence", 'INTEGER DEFAULT 0'),
        ]:
            try:
                conn.execute(f"ALTER TABLE leads ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass  # column already exists
        conn.commit()
        logger.info("Database initialised at %s", DB_PATH)
    finally:
        conn.close()


def insert_lead(name, email, phone, company, requirement,
                category="General Inquiry", priority="Medium", confidence=0):
    conn = _connect()
    try:
        cursor = conn.execute(
            '''
            INSERT INTO leads
                (name, email, phone, company, requirement, submitted_at,
                 category, priority, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (name, email, phone, company, requirement,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
             category, priority, confidence)
        )
        conn.commit()
        lead_id = cursor.lastrowid
        logger.info("Lead inserted: id=%d category=%s priority=%s", lead_id, category, priority)
        return lead_id
    finally:
        conn.close()


def mark_email_sent(lead_id):
    conn = _connect()
    try:
        conn.execute("UPDATE leads SET email_sent=1 WHERE id=?", (lead_id,))
        conn.commit()
    finally:
        conn.close()


def mark_email_opened(lead_id):
    conn = _connect()
    try:
        conn.execute("UPDATE leads SET email_opened=1 WHERE id=?", (lead_id,))
        conn.commit()
        logger.info("Email opened: lead_id=%d", lead_id)
    finally:
        conn.close()


def mark_link_clicked(lead_id):
    conn = _connect()
    try:
        conn.execute("UPDATE leads SET link_clicked=1 WHERE id=?", (lead_id,))
        conn.commit()
        logger.info("Link clicked: lead_id=%d", lead_id)
    finally:
        conn.close()


def get_all_leads():
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY submitted_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_stats():
    conn = _connect()
    try:
        c = conn.cursor()
        total   = c.execute("SELECT COUNT(*)                       FROM leads").fetchone()[0]
        sent    = c.execute("SELECT COUNT(*) FROM leads WHERE email_sent=1").fetchone()[0]
        opened  = c.execute("SELECT COUNT(*) FROM leads WHERE email_opened=1").fetchone()[0]
        clicked = c.execute("SELECT COUNT(*) FROM leads WHERE link_clicked=1").fetchone()[0]
        return {"total": total, "sent": sent, "opened": opened, "clicked": clicked}
    finally:
        conn.close()
