from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

# Ruta donde se creará la BD:
# asumiendo que db.py está en src/ y que la BD se debe llamar cokeapp.sqlite
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "src" / "cokeapp.sqlite"

print(f"Creando base de datos en: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Tabla de usuarios
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        nombre TEXT,
        tipo_plan TEXT DEFAULT 'free',  -- free, premium, admin, etc.
        api_key TEXT,
        fecha_expiracion TEXT,
        fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """
)

# ⚠️ EDITA estos correos/nombres a los tuyos antes de ejecutar
admin_email = "cokedividendos@gmail.com"
admin_nombre = "Coke"

miembro_email = "miembro_prueba@correo.com"
miembro_nombre = "Miembro Prueba"

# Opcional: ejemplo de fecha de expiración para premium (30 días desde hoy)
expira_premium = (datetime.now() + timedelta(days=30)).isoformat(timespec="seconds")

# Inserta un usuario admin
cur.execute(
    """
    INSERT OR IGNORE INTO usuarios (email, nombre, tipo_plan, api_key, fecha_expiracion)
    VALUES (?, ?, 'admin', NULL, NULL);
    """,
    (admin_email, admin_nombre),
)

# Inserta un usuario de prueba con plan 'free' (puedes cambiar a 'premium')
cur.execute(
    """
    INSERT OR IGNORE INTO usuarios (email, nombre, tipo_plan, api_key, fecha_expiracion)
    VALUES (?, ?, 'free', NULL, NULL);
    """,
    (miembro_email, miembro_nombre),
)

conn.commit()
conn.close()

print("✅ Base de datos creada/actualizada correctamente.")
