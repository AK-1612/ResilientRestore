import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any

DB_NAME = "resilient_restore.db"

def init_db():
    """Initializes the SQLite audit log database table."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            transaction_id TEXT PRIMARY KEY,
            tool_name TEXT,
            target_path TEXT,
            status TEXT,
            timestamp TEXT,
            error_detail TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_transaction(tx_id: str, tool_name: str, target_path: str, status: str, error_detail: str = None):
    """Records or updates a transaction in the SQLite audit log."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO audit_logs (transaction_id, tool_name, target_path, status, timestamp, error_detail)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (tx_id or "no_tx_id", tool_name, target_path or "N/A", status, datetime.now(timezone.utc).isoformat(), error_detail))
    conn.commit()
    conn.close()

def get_all_logs() -> List[Dict[str, Any]]:
    """Retrieves all historical audit logs ordered by latest timestamp."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_logs ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]