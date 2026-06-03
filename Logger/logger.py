import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'logs.db')


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            user        TEXT,
            action      TEXT    NOT NULL,
            source      TEXT,
            target_type TEXT,
            target_id   INTEGER,
            detail      TEXT
        )
    ''')
    conn.commit()
    return conn


def log_action(action, user=None, source=None, target_type=None, target_id=None, detail=None):
    conn = _conn()
    conn.execute(
        '''INSERT INTO logs (timestamp, user, action, source, target_type, target_id, detail)
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (datetime.utcnow().isoformat(), user, action, source, target_type, target_id, detail)
    )
    conn.commit()
    conn.close()


def get_logs(limit=200):
    conn = _conn()
    rows = conn.execute(
        'SELECT id, timestamp, user, action, source, target_type, target_id, detail '
        'FROM logs ORDER BY id DESC LIMIT ?',
        (limit,)
    ).fetchall()
    conn.close()
    return [
        dict(id=r[0], timestamp=r[1], user=r[2], action=r[3],
             source=r[4], target_type=r[5], target_id=r[6], detail=r[7])
        for r in rows
    ]

def get_record_logs(target_type, target_id, limit=50):
    conn = _conn()
    rows = conn.execute(
        'SELECT id, timestamp, user, action, source, target_type, target_id, detail '
        'FROM logs WHERE target_type = ? AND target_id = ? ORDER BY id DESC LIMIT ?',
        (target_type, target_id, limit)
    ).fetchall()
    conn.close()
    return [
        dict(id=r[0], timestamp=r[1], user=r[2], action=r[3], source=r[4], target_type=r[5], target_id=r[6], detail=r[7])
        for r in rows
    ]
