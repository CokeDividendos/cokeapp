# src/db.py

import sqlite3
from pathlib import Path
import hashlib

# Establecer el path de la base de datos
DB_PATH = Path(__file__).resolve().parent / "cokeapp.sqlite"

def init_user_table():
    """Crea la tabla de usuarios si no existe."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

def insert_user(email: str, password: str) -> bool:
    """Inserta un usuario con hash de contraseña; retorna False si ya existe."""
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (email, password_hash) VALUES (?, ?)", (email, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(email: str):
    """Obtiene la fila del usuario (email, password_hash)."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT email, password_hash FROM usuarios WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row
