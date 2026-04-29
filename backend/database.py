import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT,
            format_id TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT,
            visitor_id TEXT
        )
    ''')
    
    # Migration: Add visitor_id if it doesn't exist (for existing history.db)
    try:
        cursor.execute('ALTER TABLE downloads ADD COLUMN visitor_id TEXT')
    except sqlite3.OperationalError:
        pass # Already exists
        
    conn.commit()
    conn.close()

def add_download(job_id, url, visitor_id, title=None, format_id=None, status='started'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO downloads (id, url, visitor_id, title, format_id, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (job_id, url, visitor_id, title, format_id, status))
    conn.commit()
    conn.close()

def update_download_status(job_id, status, title=None, file_path=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if title and file_path:
        cursor.execute('''
            UPDATE downloads SET status = ?, title = ?, file_path = ? WHERE id = ?
        ''', (status, title, file_path, job_id))
    else:
        cursor.execute('''
            UPDATE downloads SET status = ? WHERE id = ?
        ''', (status, job_id))
    conn.commit()
    conn.close()

def get_history(visitor_id, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM downloads WHERE visitor_id = ? ORDER BY timestamp DESC LIMIT ?', (visitor_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def clear_history(visitor_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM downloads WHERE visitor_id = ?', (visitor_id,))
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()
