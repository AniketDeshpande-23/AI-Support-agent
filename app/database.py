import sqlite3
from datetime import datetime

DB_NAME = "support_logs.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticket_text TEXT,
            category TEXT,
            priority TEXT,
            confidence INTEGER,
            grounded BOOLEAN,
            route_to TEXT,
            reply TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_ticket(record: dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO tickets (
            timestamp,
            ticket_text,
            category,
            priority,
            confidence,
            grounded,
            route_to,
            reply
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        record["ticket_text"],
        record["category"],
        record["priority"],
        record["confidence"],
        record["grounded"],
        record["route_to"],
        record["reply"]
    ))

    conn.commit()
    conn.close()
