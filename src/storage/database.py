from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager

from src.config import DATABASE_PATH, ensure_dirs
from src.utils.logger import get_logger

logger = get_logger(__name__)

_connection: sqlite3.Connection | None = None
_lock = threading.Lock()


def _get_or_create_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


@contextmanager
def get_connection():
    """Provide the shared SQLite connection under a lock."""
    with _lock:
        conn = _get_or_create_connection()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise


def init_db() -> None:
    """Create all tables if they don't exist."""
    ensure_dirs()
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                sector TEXT NOT NULL DEFAULT 'other',
                company_type TEXT NOT NULL DEFAULT 'unknown',
                funding_stage TEXT,
                product_name TEXT NOT NULL DEFAULT '',
                location TEXT,
                website_url TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL DEFAULT '',
                source_type TEXT NOT NULL DEFAULT 'web_search',
                tech_stack TEXT NOT NULL DEFAULT '[]',
                jetson_usage TEXT,
                jetson_models TEXT NOT NULL DEFAULT '[]',
                jetson_confirmed INTEGER NOT NULL DEFAULT 0,
                user_rating INTEGER,
                feedback TEXT,
                campaign TEXT NOT NULL DEFAULT '',
                summary TEXT NOT NULL DEFAULT '',
                discovered_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS blocked_companies (
                company_name TEXT PRIMARY KEY,
                blocked_at TEXT NOT NULL,
                reason TEXT DEFAULT ''
            );

            -- Recreate unique index with case-insensitive collation
            DROP INDEX IF EXISTS idx_leads_company_campaign;
            CREATE UNIQUE INDEX idx_leads_company_campaign
                ON leads(company_name COLLATE NOCASE, campaign COLLATE NOCASE);
            CREATE INDEX IF NOT EXISTS idx_leads_discovered
                ON leads(discovered_at DESC);
        """)
        conn.commit()
        logger.info(f"Database initialized at {DATABASE_PATH}")
