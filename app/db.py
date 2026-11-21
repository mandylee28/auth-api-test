"""SQLite storage for users. stdlib sqlite3 only, no new dependency."""

import os
import sqlite3
from pathlib import Path

SEEDED_USERS = {"alice@example.com": "Passw0rd!", "bob@example.com": "BobPass123!"}

DB_PATH = Path(os.environ.get("AUTH_DB_PATH", "auth.db"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the users table and seed alice and bob (if missing)."""
    with _connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password TEXT NOT NULL)"
        )
        for email, password in SEEDED_USERS.items():
            conn.execute(
                "INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)",
                (email, password),
            )


def get_password(email: str) -> str | None:
    """Password for the email, or None if the user does not exist."""
    with _connect() as conn:
        row = conn.execute("SELECT password FROM users WHERE email = ?", (email,)).fetchone()
        return row["password"] if row else None


def create_user(email: str, password: str) -> bool:
    """Insert a user; False if the email is already registered."""
    try:
        with _connect() as conn:
            conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
    except sqlite3.IntegrityError:
        return False
    return True


def reset_users() -> None:
    """Test-only: drop all users and re-seed alice and bob."""
    with _connect() as conn:
        conn.execute("DELETE FROM users")
        for email, password in SEEDED_USERS.items():
            conn.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password),
            )
