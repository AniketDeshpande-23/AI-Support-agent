"""
app/database.py — SQLite persistence layer.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any

from app.config import get_settings

_settings = get_settings()
DB_NAME = _settings.DB_PATH


@contextmanager
def _conn():
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
                reply       TEXT,
                customer_id TEXT    DEFAULT '',
                thread_id   TEXT    DEFAULT ''
            )
        """)
        # Migrate existing DBs that lack the new columns
        for col, definition in [("customer_id", "TEXT DEFAULT ''"),
                                  ("thread_id",   "TEXT DEFAULT ''")]:
            try:
                conn.execute(f"ALTER TABLE tickets ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass  # column already exists

        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id           INTEGER NOT NULL,
                timestamp           TEXT    NOT NULL,
                approved            BOOLEAN NOT NULL,
                corrected_category  TEXT    DEFAULT NULL,
                corrected_reply     TEXT    DEFAULT NULL,
                FOREIGN KEY (ticket_id) REFERENCES tickets(id)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_thread   ON tickets(thread_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets(customer_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_ticket  ON feedback(ticket_id)")


# ── Writes ────────────────────────────────────────────────────────────────────

def save_ticket(record: dict) -> int:
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tickets
                (timestamp, ticket_text, category, priority,
                 confidence, grounded, route_to, reply,
                 customer_id, thread_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                record.get("customer_id", ""),
                record.get("thread_id", ""),
            ),
        )
        return cur.lastrowid


def save_feedback(ticket_id: int, approved: bool,
                  corrected_category: str | None,
                  corrected_reply: str | None) -> int:
    with _conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO feedback
                (ticket_id, timestamp, approved, corrected_category, corrected_reply)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, datetime.now().isoformat(),
             approved, corrected_category, corrected_reply),
        )
        return cur.lastrowid


def cleanup_old_tickets(days: int) -> int:
    """Delete tickets older than N days. Returns deleted count."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    with _conn() as conn:
        cur = conn.execute("DELETE FROM tickets WHERE timestamp < ?", (cutoff,))
        return cur.rowcount


# ── Reads ─────────────────────────────────────────────────────────────────────

def get_tickets(limit: int = 20, offset: int = 0,
                route_filter: str | None = None) -> list[dict]:
    with _conn() as conn:
        if route_filter:
            rows = conn.execute(
                "SELECT * FROM tickets WHERE route_to = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                (route_filter, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tickets ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
    return [dict(r) for r in rows]


def get_thread_tickets(thread_id: str, limit: int = 5) -> list[dict]:
    """Return recent tickets for a thread (oldest first for context)."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM tickets WHERE thread_id = ? ORDER BY id DESC LIMIT ?",
            (thread_id, limit),
        ).fetchall()
    return list(reversed([dict(r) for r in rows]))


def get_ticket_by_id(ticket_id: int) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
    return dict(row) if row else None


def get_metrics() -> dict[str, Any]:
    with _conn() as conn:
        total        = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        by_category  = conn.execute(
            "SELECT category, COUNT(*) AS cnt FROM tickets GROUP BY category"
        ).fetchall()
        by_priority  = conn.execute(
            "SELECT priority, COUNT(*) AS cnt FROM tickets GROUP BY priority"
        ).fetchall()
        avg_conf     = round(
            conn.execute("SELECT AVG(confidence) FROM tickets").fetchone()[0] or 0.0, 1
        )
        human_review = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE route_to = 'Human Review'"
        ).fetchone()[0]
        grounding    = conn.execute(
            "SELECT ROUND(AVG(CAST(grounded AS REAL)) * 100, 1) FROM tickets"
        ).fetchone()[0] or 0.0
    return {
        "total":              total,
        "avg_confidence":     avg_conf,
        "human_review_count": human_review,
        "grounding_rate":     grounding,
        "by_category":        {r["category"]: r["cnt"] for r in by_category},
        "by_priority":        {r["priority"]: r["cnt"] for r in by_priority},
    }
