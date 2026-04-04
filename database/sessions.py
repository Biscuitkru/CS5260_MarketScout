"""
MarketScout: Session Persistence
=================================
SQLite storage for chat sessions
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent/"sessions.db"

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                messages TEXT NOT NULL,
                pipeline_context TEXT,
                report TEXT
            )
        """)

def save_session(
    session_id: str,
    title: str,
    messages: list[dict],
    pipeline_context: dict | None = None,
    report: str | None = None,
):
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        existing = conn.execute(
            "SELECT created_at FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        created = existing["created_at"] if existing else now

        conn.execute(
            """
            INSERT INTO sessions (id, title, created_at, updated_at, messages, pipeline_context, report)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                updated_at = excluded.updated_at,
                messages = excluded.messages,
                pipeline_context = excluded.pipeline_context,
                report = excluded.report
            """,
            (
                session_id,
                title,
                created,
                now,
                json.dumps(messages),
                json.dumps(pipeline_context) if pipeline_context else None,
                report,
            ),
        )

def list_sessions(limit: int = 20) -> list[dict]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM sessions "
            "ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

def load_session(session_id: str) -> dict | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["messages"] = json.loads(data["messages"])
        data["pipeline_context"] = (
            json.loads(data["pipeline_context"])
            if data["pipeline_context"]
            else None
        )
        return data

def rename_session(session_id: str, new_title: str):
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
            (new_title, now, session_id),
        )

def delete_session(session_id: str):
    with _get_conn() as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

init_db()
