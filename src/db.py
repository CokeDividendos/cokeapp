import sqlite3
from pathlib import Path
import datetime

DB_PATH = Path(__file__).parent / "cokeapp.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Tabla usuarios
    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nombre TEXT,
        tipo_plan TEXT DEFAULT 'free', -- free, premium, admin
        api_key TEXT,
        fecha_expiracion TEXT,
        fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Usuario admin por defecto (modifica el email/nombre si quieres)
    cur.execute("SELECT * FROM usuarios WHERE email = ?", ("admin@tudominio.com",))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO usuarios (email, nombre, tipo_plan)
            VALUES (?, ?, 'admin')
        """, ("admin@tudominio.com", "Administrador"))
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
    cur.execute("UPDATE usuarios SET tipo_plan = ?, fecha_expiracion = ? WHERE email = ?", (tipo_plan, fecha_expiracion, email))
    conn.commit()
    conn.close()

def set_user_api_key(email, api_key):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET api_key = ? WHERE email = ?", (api_key, email))
    conn.commit()
    conn.close()
