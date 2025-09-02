import sqlite3
from config import cfg

def get_conn():
    conn = sqlite3.connect(cfg.db_path)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS jobs(
        id TEXT PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        url TEXT,
        source TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS applications(
        job_id TEXT PRIMARY KEY,
        status TEXT,
        applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    );
    """)
    return conn

def upsert_job(job_id: str, title: str, company: str, location: str, url: str, source: str):
    conn = get_conn()
    with conn:
        conn.execute("""
        INSERT OR IGNORE INTO jobs(id, title, company, location, url, source)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (job_id, title, company, location, url, source))
    conn.close()

def mark_applied(job_id: str, status: str = "submitted", notes: str = ""):
    conn = get_conn()
    with conn:
        conn.execute("""
        INSERT OR REPLACE INTO applications(job_id, status, notes)
        VALUES (?, ?, ?)
        """, (job_id, status, notes))
    conn.close()

def is_applied(job_id: str) -> bool:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM applications WHERE job_id = ? LIMIT 1", (job_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None
