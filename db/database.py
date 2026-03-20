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
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre            TEXT    NOT NULL,
            precio            REAL    NOT NULL,
            cantidad          INTEGER NOT NULL DEFAULT 0,
            categoria         TEXT,
            descuento_pct     REAL    NOT NULL DEFAULT 0,
            descuento_activo  INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ventas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor_id INTEGER NOT NULL,
            total       REAL    NOT NULL,
            fecha       TEXT    NOT NULL,
            FOREIGN KEY (vendedor_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS detalle_venta (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id       INTEGER NOT NULL,
            producto_id    INTEGER NOT NULL,
            cantidad       INTEGER NOT NULL,
            precio_unit    REAL    NOT NULL,
            descuento_monto REAL   NOT NULL DEFAULT 0,
            FOREIGN KEY (venta_id)    REFERENCES ventas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );
                         
        CREATE TABLE IF NOT EXISTS permisos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            modulo TEXT NOT NULL,
            permitido INTEGER NOT NULL DEFAULT 1,
            UNIQUE(usuario_id, modulo),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
                         
    """)

    # Migración: agregar columnas faltantes si no existen
    cursor.execute("PRAGMA table_info(productos)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "descuento_pct" not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN descuento_pct REAL NOT NULL DEFAULT 0")
    
    if "descuento_activo" not in columns:
        cursor.execute("ALTER TABLE productos ADD COLUMN descuento_activo INTEGER NOT NULL DEFAULT 0")
    
    cursor.execute("PRAGMA table_info(detalle_venta)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "descuento_monto" not in columns:
        cursor.execute("ALTER TABLE detalle_venta ADD COLUMN descuento_monto REAL NOT NULL DEFAULT 0")

    # Usuarios por defecto
    cursor.executemany("""
        INSERT OR IGNORE INTO usuarios (nombre, usuario, password, rol)
        VALUES (?, ?, ?, ?)
    """, [
        ("Administrador", "admin",    "admin123",    "admin"),
    ])

    # Productos de prueba (solo si la tabla está vacía)
    cursor.execute("SELECT COUNT(*) FROM productos")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO productos (nombre, precio, cantidad, categoria)
            VALUES (?, ?, ?, ?)
        """, [
            # Bebidas
            ("Agua Botella 500ml",          1500,  80, "Bebidas"),
            ("Jugo de Naranja Natural",      4500,  40, "Bebidas"),
            ("Gaseosa Cola 350ml",           2500,  60, "Bebidas"),
            ("Té Frío Limón 400ml",          3000,  35, "Bebidas"),
            ("Café Americano",               3500,  50, "Bebidas"),
            # Snacks
            ("Papas Fritas Bolsa 150g",      3200,  45, "Snacks"),
            ("Maní Salado 100g",             2800,  30, "Snacks"),
            ("Galletas Integrales 200g",     4000,  25, "Snacks"),
            ("Barra de Cereal Avena",        2200,  55, "Snacks"),
            ("Chitos Maíz 80g",              2000,  40, "Snacks"),
            # Lácteos
            ("Leche Entera 1L",              4200,  30, "Lácteos"),
            ("Yogur Fresa 200g",             3800,  20, "Lácteos"),
            ("Queso Campesino 250g",         6500,  15, "Lácteos"),
            ("Kumis 200ml",                  2900,  25, "Lácteos"),
            # Panadería
            ("Pan Tajado Integral",          5500,  20, "Panadería"),
            ("Croissant Mantequilla",        3500,  18, "Panadería"),
            ("Almojábana",                   1800,  30, "Panadería"),
            ("Pandebono",                    2000,  35, "Panadería"),
            # Platos
            ("Bandeja Paisa",               18000,  10, "Platos"),
            ("Arroz con Pollo",             14000,  12, "Platos"),
            ("Sopa de Lentejas",             9000,  15, "Platos"),
            ("Empanada de Pipián",           2500,  40, "Platos"),
            ("Arepas con Queso x2",          4500,  25, "Platos"),
        ])

    conn.commit()
    conn.close()