import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acceder a columnas por nombre
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT    NOT NULL,
            usuario   TEXT    NOT NULL UNIQUE,
            password  TEXT    NOT NULL,
            rol       TEXT    NOT NULL CHECK(rol IN ('admin', 'vendedor')),
            activo    INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS productos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre    TEXT    NOT NULL,
            precio    REAL    NOT NULL,
            cantidad  INTEGER NOT NULL DEFAULT 0,
            categoria TEXT
        );

        CREATE TABLE IF NOT EXISTS ventas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor_id INTEGER NOT NULL,
            total       REAL    NOT NULL,
            fecha       TEXT    NOT NULL,
            FOREIGN KEY (vendedor_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS detalle_venta (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id    INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad    INTEGER NOT NULL,
            precio_unit REAL    NOT NULL,
            FOREIGN KEY (venta_id)    REFERENCES ventas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );
    """)

    # Usuarios por defecto
    cursor.executemany("""
        INSERT OR IGNORE INTO usuarios (nombre, usuario, password, rol)
        VALUES (?, ?, ?, ?)
    """, [
        ("Administrador", "admin",    "admin123",    "admin"),
        ("Vendedor Demo", "vendedor", "vendedor123", "vendedor"),
    ])

    conn.commit()
    conn.close()