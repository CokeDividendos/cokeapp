# src/db.py
import sqlite3
from pathlib import Path
import datetime

# La BD se guardará junto a este archivo
DB_PATH = Path(__file__).parent / "cokeapp.sqlite"

def listar_usuarios():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, email, nombre FROM usuarios")
    rows = cur.fetchall()
    conn.close()
    return rows

def init_db():
    """
    Crea la tabla de usuarios si no existe y agrega un usuario admin
    con tu correo. Si ya existe, lo deja intacto.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nombre TEXT,
        tipo_plan TEXT DEFAULT 'free',  -- free, premium, admin
        api_key TEXT,
        fecha_expiracion TEXT,
        fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # ⚠️ Sustituye el correo y el nombre con los tuyos antes de guardar el archivo
    default_admin_email = cokedividendos@gmail.com
    default_admin_nombre = Coke
    cur.execute("SELECT * FROM usuarios WHERE email = ?", (default_admin_email,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO usuarios (email, nombre, tipo_plan)
            VALUES (?, ?, 'admin')
        """, (default_admin_email, default_admin_nombre))
        conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()
    return user

def update_user_plan(email, tipo_plan, fecha_expiracion=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE usuarios SET tipo_plan = ?, fecha_expiracion = ? WHERE email = ?",
        (tipo_plan, fecha_expiracion, email)
    )
    conn.commit()
    conn.close()

def set_user_api_key(email, api_key):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "UPDATE usuarios SET api_key = ? WHERE email = ?",
        (api_key, email)
    )
    conn.commit()
    conn.close()

def upsert_user(email: str, **fields) -> None:
    """Update or insert a user record with the given fields."""
    if not fields:
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    placeholders = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [email]
    cur.execute(f"UPDATE usuarios SET {placeholders} WHERE email = ?", values)
    if cur.rowcount == 0:
        cols = ",".join(["email"] + list(fields.keys()))
        qs = ",".join(["?"] * (len(fields) + 1))
        cur.execute(
            f"INSERT INTO usuarios ({cols}) VALUES ({qs})",
            [email, *fields.values()]
        )
    conn.commit()
    conn.close()
