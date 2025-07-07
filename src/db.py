import sqlite3
from pathlib import Path
from typing import Optional, Dict

DB_PATH = Path(__file__).resolve().parent / "users.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                email TEXT PRIMARY KEY,
                api_key TEXT,
                portfolio TEXT,
                plan TEXT DEFAULT 'beta'
            )
            """
        )
        conn.commit()


# Initialize database on import
init_db()


def get_user(email: str) -> Optional[Dict[str, str]]:
    """Return user data as dict or None."""
    with _get_connection() as conn:
        cur = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def upsert_user(**fields) -> None:
    """Insert or update user by email."""
    if "email" not in fields:
        raise ValueError("email is required")
    columns = list(fields.keys())
    placeholders = ",".join(["?"] * len(columns))
    assignments = ",".join(
        f"{c}=excluded.{c}" for c in columns if c != "email"
    )
    sql = f"INSERT INTO users ({','.join(columns)}) VALUES ({placeholders})"
    if assignments:
        sql += f" ON CONFLICT(email) DO UPDATE SET {assignments}"
    values = tuple(fields[c] for c in columns)
    with _get_connection() as conn:
        conn.execute(sql, values)
        conn.commit()
