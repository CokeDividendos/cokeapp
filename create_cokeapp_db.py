from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

# Ruta de la BD (coincide con DB_PATH en db.py)
DB_PATH = Path(__file__).resolve().parent / "src" / "cokeapp.sqlite"

# Lista de usuarios permitidos
usuarios = [
    {
        "email": cokedividendos@gmail.com,
        "nombre": Coke,
        "tipo_plan": "admin",
        "fecha_expiracion": None  # No expira
    },
    {
        "email": "otro_miembro@correo.com",
        "nombre": "Miembro Ejemplo",
        "tipo_plan": "free",
        "fecha_expiracion": None
    },
    # Agrega tantos usuarios como necesites...
]

# Crea la tabla
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    nombre TEXT,
    tipo_plan TEXT DEFAULT 'free',
    api_key TEXT,
    fecha_expiracion TEXT,
    fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
);
""")
# Inserta cada usuario
for u in usuarios:
    cur.execute("""
    INSERT OR IGNORE INTO usuarios
    (email, nombre, tipo_plan, fecha_expiracion)
    VALUES (?, ?, ?, ?)
    """, (u["email"], u["nombre"], u["tipo_plan"], u["fecha_expiracion"]))
conn.commit()
conn.close()
print(f"BD creada en {DB_PATH}")

