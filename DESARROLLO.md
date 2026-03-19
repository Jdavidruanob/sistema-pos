# Documentación de Desarrollo — Mini-Sistema POS

## Índice
1. [Resumen del proyecto](#resumen-del-proyecto)
2. [Arquitectura general](#arquitectura-general)
3. [Base de datos](#base-de-datos)
4. [Módulo de autenticación](#módulo-de-autenticación)
5. [Módulo de inventario](#módulo-de-inventario)
6. [Módulo de ventas (backend)](#módulo-de-ventas-backend)
7. [Interfaz de ventas (HU-07)](#interfaz-de-ventas-hu-07)
8. [Datos de prueba](#datos-de-prueba)
9. [Instalación y ejecución](#instalación-y-ejecución)

---

## Resumen del proyecto

**Mini-Sistema POS** es una aplicación de escritorio para registro de ventas, gestión de inventario y reportes. Está construido con:

- **Python 3.13** como lenguaje principal
- **PySide6** para la interfaz gráfica (Qt)
- **SQLite** como base de datos local (sin servidor)

---

## Arquitectura general

```
sistema-pos/
├── main.py              # Punto de entrada de la aplicación
├── config.py            # Configuración global (rutas, nombre de app)
├── requirements.txt     # Dependencias Python
│
├── db/
│   └── database.py      # Conexión y creación de tablas
│
├── auth/
│   ├── login.py         # Lógica de autenticación
│   └── session.py       # Sesión del usuario en memoria
│
├── modules/
│   ├── inventory.py     # Lógica de negocio: inventario
│   ├── sales.py         # Lógica de negocio: ventas
│   └── reports.py       # Lógica de negocio: reportes (pendiente)
│
└── ui/
    ├── login_window.py  # Ventana de inicio de sesión
    ├── main_window.py   # Ventana principal con sidebar y navegación
    └── sales_page.py    # Página del módulo de ventas (HU-07)
```

### Flujo de arranque

```
main.py
  │
  ├── init_db()          → Crea tablas y datos por defecto en SQLite
  └── LoginWindow()      → Muestra la ventana de login
        └── (login exitoso)
              └── MainWindow() → Ventana principal con módulos
```

---

## Base de datos

**Archivo:** `db/database.py`

### Tablas creadas

```sql
-- Usuarios del sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT    NOT NULL,
    usuario   TEXT    NOT NULL UNIQUE,
    password  TEXT    NOT NULL,
    rol       TEXT    NOT NULL CHECK(rol IN ('admin', 'vendedor')),
    activo    INTEGER NOT NULL DEFAULT 1
);

-- Catálogo de productos
CREATE TABLE IF NOT EXISTS productos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT    NOT NULL,
    precio    REAL    NOT NULL,
    cantidad  INTEGER NOT NULL DEFAULT 0,
    categoria TEXT
);

-- Cabecera de cada venta
CREATE TABLE IF NOT EXISTS ventas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    vendedor_id INTEGER NOT NULL,
    total       REAL    NOT NULL,
    fecha       TEXT    NOT NULL,
    FOREIGN KEY (vendedor_id) REFERENCES usuarios(id)
);

-- Líneas de cada venta (productos vendidos)
CREATE TABLE IF NOT EXISTS detalle_venta (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id    INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad    INTEGER NOT NULL,
    precio_unit REAL    NOT NULL,
    FOREIGN KEY (venta_id)    REFERENCES ventas(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);
```

### Funciones implementadas

| Función | Descripción |
|---|---|
| `get_connection()` | Abre una conexión SQLite con `row_factory = sqlite3.Row` para acceder columnas por nombre |
| `init_db()` | Crea tablas, inserta usuarios por defecto y productos de prueba si la tabla está vacía |

---

## Módulo de autenticación

### `auth/login.py` — función `login(usuario, password)`

1. Consulta la BD buscando un usuario activo con las credenciales dadas.
2. Si lo encuentra, llama a `set_session()` con los datos del usuario.
3. Retorna `{"success": True, "data": {...}}` o `{"success": False, "error": "..."}`.

> ⚠️ Las contraseñas se guardan en texto plano (sin hash). Para producción se debería usar `bcrypt` o similar.

### `auth/session.py` — sesión en memoria

Implementa una sesión global usando un diccionario `current_user`:

```python
current_user = { "id": None, "nombre": None, "usuario": None, "rol": None }
```

| Función | Descripción |
|---|---|
| `set_session(user_data)` | Guarda los datos del usuario autenticado |
| `get_session()` | Retorna el usuario actual |
| `clear_session()` | Limpia la sesión (logout) |
| `is_authenticated()` | `True` si hay un usuario activo |
| `is_admin()` | `True` si el rol es `"admin"` |

### Credenciales por defecto

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `vendedor` | `vendedor123` | Vendedor |

---

## Módulo de inventario

**Archivo:** `modules/inventory.py` — clase `InventoryManager`

### Métodos implementados

#### `get_all()`
Consulta todos los productos ordenados por nombre.

```python
def get_all(self):
    # SELECT id, nombre, precio, cantidad, categoria FROM productos ORDER BY nombre
    # Retorna: {"success": True, "data": [lista de dicts]}
```

#### `discount_stock(producto_id, cantidad)`
Descuenta unidades del stock de un producto. Valida que:
- El producto exista.
- Haya suficiente stock antes de descontar.

```python
def discount_stock(self, producto_id, cantidad):
    # Valida existencia y stock suficiente
    # UPDATE productos SET cantidad = cantidad - ? WHERE id = ?
    # Retorna: {"success": True, "data": None} o {"success": False, "error": "..."}
```

### Métodos pendientes (esqueleto)

- `get_by_id(producto_id)`
- `add(nombre, precio, cantidad, categoria)`
- `update(producto_id, nombre, precio, cantidad, categoria)`
- `delete(producto_id)`

---

## Módulo de ventas (backend)

**Archivo:** `modules/sales.py` — clase `SalesManager`

### `create_sale(vendedor_id, items)`

Registra una venta completa de forma **atómica** (todo o nada en una sola transacción).

**Parámetros:**
```python
vendedor_id = 1   # ID del usuario autenticado

items = [
    {"producto_id": 1, "cantidad": 2, "precio_unit": 5000},
    {"producto_id": 3, "cantidad": 1, "precio_unit": 12000},
]
```

**Flujo interno:**

```
Paso 1 — Validación previa (sin tocar la BD)
  └── Por cada item: verifica que el producto exista y tenga stock suficiente
  └── Si algo falla → retorna error inmediatamente

Paso 2 — Calcular total
  └── total = Σ (cantidad × precio_unit)

Paso 3 — Insertar cabecera en tabla `ventas`
  └── vendedor_id, total, fecha (datetime actual)
  └── Guarda el venta_id generado

Paso 4 — Por cada item (misma transacción):
  └── INSERT en detalle_venta
  └── UPDATE productos SET cantidad = cantidad - ?

Paso 5 — conn.commit()
  └── Si ocurre cualquier error → rollback automático
```

**¿Por qué todo en una transacción?**

Si se usara una conexión separada para descontar el stock, podría quedar la venta registrada pero el stock sin actualizar si hay un error entre ambas operaciones. Con una sola transacción, SQLite garantiza que o todo se guarda o nada cambia.

**Retorna:**
```python
{"success": True,  "data": venta_id}     # éxito
{"success": False, "error": "mensaje"}   # fallo
```

### Patrón de respuesta unificado

Todos los módulos retornan siempre el mismo formato, lo que facilita el manejo de errores en la UI:

```python
{"success": True,  "data": ...}
{"success": False, "error": "..."}
```

---

## Interfaz de ventas (HU-07)

**Historia de usuario:** *Como vendedor, quiero registrar una venta seleccionando productos y cantidades, para guardar la transacción y actualizar el stock automáticamente.*

**Archivo:** `ui/sales_page.py` — clase `SalesPage(QWidget)`

### Layout general

```
┌─────────────────────────────────────────────────────────┐
│ 🛒  Registrar Venta                                     │
├──────────────────────────────┬──────────────────────────┤
│  PANEL IZQUIERDO             │  PANEL DERECHO           │
│  (stretch=3)                 │  (stretch=2)             │
│                              │                          │
│  Productos disponibles       │  Carrito de venta        │
│  ┌──────────────────────┐    │  ┌────────────────────┐  │
│  │ 🔍 Buscar...         │    │  │ Producto│Cant│Sub  │  │
│  ├──────────────────────┤    │  │ ...     │... │...  │  │
│  │ ID│Nombre│Cat│$│Stock│    │  └────────────────────┘  │
│  │ ..│ ...  │...│.│ ... │    │                          │
│  └──────────────────────┘    │  TOTAL: $ 0              │
│                              │                          │
│  Cantidad: [1] [➕ Agregar]  │  [🗑 Vaciar] [✅ Confirmar]│
└──────────────────────────────┴──────────────────────────┘
```

### Funcionalidades implementadas

| Criterio HU-07 | Implementación |
|---|---|
| Buscar y seleccionar productos | Barra de búsqueda que filtra por nombre y categoría en tiempo real (`textChanged`) |
| Especificar cantidad | `QSpinBox` (mín. 1, máx. 9999) antes de agregar. También disponible con doble clic en la fila |
| Total automático | Se recalcula en `_refresh_cart()` en cada cambio del carrito |
| Guardar con fecha, hora y vendedor | `datetime.now()` + `get_session()["id"]` en `create_sale()` |
| Stock descuenta automáticamente | La BD se actualiza en la misma transacción; la tabla de productos se recarga al confirmar |
| Resumen al finalizar | Diálogo modal (`QDialog`) con ID de venta, vendedor, items y total |
| No vender más del stock | Validación doble: cantidad individual y acumulada en el carrito |

### Métodos clave

```python
_load_products()          # Carga productos desde BD via InventoryManager.get_all()
_filter_products(text)    # Filtra la tabla en tiempo real por nombre/categoría
_add_selected_to_cart()   # Valida stock y agrega/acumula en el carrito
_refresh_cart()           # Re-dibuja la tabla del carrito y actualiza el total
_confirm_sale()           # Llama a SalesManager.create_sale() y muestra resumen
_show_summary(venta_id)   # Diálogo modal con el resumen de la venta registrada
_clear_cart()             # Vacía el carrito con confirmación previa
_remove_from_cart(idx)    # Elimina un item individual del carrito
```

### Integración en `main_window.py`

```python
from ui.sales_page import SalesPage

self.pages = {
    "inventario": self._placeholder("Módulo de Inventario"),
    "ventas":     SalesPage(),          # ← página real conectada
    "reportes":   self._placeholder("Módulo de Reportes"),
}
```

---

## Datos de prueba

Se agregaron **23 productos de comida** en `db/database.py`, que se insertan automáticamente cuando la tabla `productos` está vacía:

| Categoría | Productos |
|---|---|
| Bebidas | Agua 500ml, Jugo de naranja, Gaseosa Cola, Té frío limón, Café americano |
| Snacks | Papas fritas, Maní salado, Galletas integrales, Barra de cereal, Chitos |
| Lácteos | Leche entera, Yogur fresa, Queso campesino, Kumis |
| Panadería | Pan tajado integral, Croissant, Almojábana, Pandebono |
| Platos | Bandeja paisa, Arroz con pollo, Sopa de lentejas, Empanada de pipián, Arepas con queso |

---

## Instalación y ejecución

### Primera vez

```bash
cd sistema-pos

# Crear entorno virtual
python -m venv venv

# Activar el entorno
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

### Ejecuciones siguientes

```bash
source venv/bin/activate
python main.py
```

### Resetear la base de datos

Si necesitas reiniciar los datos (por ejemplo, para que los productos de prueba se inserten de nuevo):

```bash
rm db/pos.db
python main.py
```
