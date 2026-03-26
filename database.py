"""
PostgreSQL (Neon) persistence for phonics-assessment-backend.

Set DATABASE_URL in .env (Neon connection string).
"""

from __future__ import annotations

import os
from typing import Any, Dict

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

psycopg: Any = None
dict_row: Any = None
Json: Any = None


def _load_psycopg():
    global psycopg, dict_row, Json
    if psycopg is None:
        import psycopg as _psycopg
        from psycopg.rows import dict_row as _dict_row
        from psycopg.types.json import Json as _Json

        psycopg = _psycopg
        dict_row = _dict_row
        Json = _Json


_EXPECTED_TABLES = frozenset({"phonics_sessions", "phonics_reports"})


def _normalize_database_url(url: str) -> str:
    u = url.strip()
    if u.startswith("postgres://"):
        u = "postgresql://" + u[len("postgres://") :]
    return u


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add your Neon connection string to .env"
        )
    return _normalize_database_url(url)


def get_connection():
    _load_psycopg()
    return psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
        connect_timeout=int(os.environ.get("PGCONNECT_TIMEOUT", "15")),
    )


def _schema_complete(conn) -> bool:
    _load_psycopg()
    cur = conn.execute(
        """
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """
    )
    found = {row["table_name"] for row in cur.fetchall()}
    return _EXPECTED_TABLES.issubset(found)


def init_db() -> None:
    """Create tables only when the full schema is missing; never drops data."""
    _load_psycopg()
    print("[phonics-backend] init_db(): connecting...", flush=True)
    conn = get_connection()
    try:
        if _schema_complete(conn):
            print(
                "[phonics-backend] init_db(): schema present — skipping CREATE TABLE",
                flush=True,
            )
            return
        print("[phonics-backend] init_db(): creating tables...", flush=True)
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS phonics_sessions (
                    session_id TEXT PRIMARY KEY,
                    data JSONB NOT NULL DEFAULT '{}'::jsonb
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS phonics_reports (
                    report_id TEXT PRIMARY KEY,
                    data JSONB NOT NULL DEFAULT '{}'::jsonb
                )
                """
            )
        conn.commit()
        print("[phonics-backend] init_db(): tables created OK", flush=True)
    finally:
        conn.close()


def _empty_store() -> Dict[str, Dict[str, Any]]:
    return {"sessions": {}, "reports": {}}


def load_payment_store() -> Dict[str, Any]:
    """Load payment/session state (replaces payments.json)."""
    _load_psycopg()
    conn = get_connection()
    try:
        cur = conn.execute("SELECT session_id, data FROM phonics_sessions")
        sessions: Dict[str, Any] = {}
        for row in cur.fetchall():
            d = row["data"]
            sessions[row["session_id"]] = d if isinstance(d, dict) else {}

        cur = conn.execute("SELECT report_id, data FROM phonics_reports")
        reports: Dict[str, Any] = {}
        for row in cur.fetchall():
            d = row["data"]
            reports[row["report_id"]] = d if isinstance(d, dict) else {}

        return {"sessions": sessions, "reports": reports}
    finally:
        conn.close()


def save_payment_store(store: Dict[str, Any]) -> None:
    """Persist full payment store (normalized shape: sessions + reports)."""
    _load_psycopg()
    sessions = dict(store.get("sessions") or {})
    reports = dict(store.get("reports") or {})
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM phonics_sessions")
            cur.execute("DELETE FROM phonics_reports")
            for sid, data in sessions.items():
                cur.execute(
                    "INSERT INTO phonics_sessions (session_id, data) VALUES (%s, %s)",
                    (sid, Json(data)),
                )
            for rid, data in reports.items():
                cur.execute(
                    "INSERT INTO phonics_reports (report_id, data) VALUES (%s, %s)",
                    (rid, Json(data)),
                )
        conn.commit()
    finally:
        conn.close()
