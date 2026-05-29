"""
app/database.py — SQLite persistence layer.

Uses a context manager for safe connection handling (auto-commit / auto-rollback).
Added get_tickets() and get_metrics() to power the /tickets and /metrics endpoints.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from app.config import get_settings

_settings = get_settings()
DB_NAME = _settings.DB_PATH


@contextmanager
def _conn():
    """Yield a connection that auto-commits or rolls back on error."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema ────────────────────────────────────────────────────────────────────

def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT    NOT NULL,
                ticket_text TEXT    NOT NULL,
                category    TEXT,
                priority    TEXT,
                confidence  INTEGER,
                grounded    BOOLEAN,
                route_to    TEXT,
                reply       TEXT
            )
        """)


# ── Writes ────────────────────────────────────────────────────────────────────

def save_ticket(record: dict) -> None:
    with _conn() as conn:
        conn.execute(
            """
            INSERT INTO tickets
                (timestamp, ticket_text, category, priority, confidence, grounded, route_to, reply)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(),
                record["ticket_text"],
                record["category"],
                record["priority"],
                record["confidence"],
                record["grounded"],
                record["route_to"],
                record["reply"],
            ),
        )


# ── Reads ─────────────────────────────────────────────────────────────────────

def get_tickets(limit: int = 20, offset: int = 0) -> list[dict]:
    """Return the most recent tickets (newest first)."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def get_metrics() -> dict[str, Any]:
    """Aggregate stats used by the /metrics endpoint and the UI history tab."""
    with _conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]

        by_category = conn.execute(
            "SELECT category, COUNT(*) AS cnt FROM tickets GROUP BY category"
        ).fetchall()

        by_priority = conn.execute(
            "SELECT priority, COUNT(*) AS cnt FROM tickets GROUP BY priority"
        ).fetchall()

        avg_conf_row = conn.execute("SELECT AVG(confidence) FROM tickets").fetchone()
        avg_conf = round(avg_conf_row[0] or 0.0, 1)

    return {
        "total": total,
        "avg_confidence": avg_conf,
        "by_category": {r["category"]: r["cnt"] for r in by_category},
        "by_priority": {r["priority"]: r["cnt"] for r in by_priority},
    }
