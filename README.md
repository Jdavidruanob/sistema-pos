# Mini-Sistema POS — Empresa XYZ

Sistema de punto de venta desarrollado con Python + PySide6 + SQLite.

---

## ⚙️ Requisitos
- Python 3.11+

---

## 🚀 Instalación

**1. Clonar el repositorio**
```bash
git clone <url-del-repo>
cd Sistema-POS
```

**2. Crear entorno virtual**
```bash
python -m venv venv
```

**3. Activar entorno virtual**

Windows:
```bash
venv\Scripts\activate
```
Mac/Linux:
```bash
source venv/bin/activate
```

**4. Instalar dependencias**
```bash
pip install -r requirements.txt
```

**5. Correr la app**
```bash
python main.py
```

---

## 👤 Usuarios de prueba

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| admin | admin123 | Administrador |
| vendedor | vendedor123 | Vendedor |

---

## 🔐 Roles

| Sección | Admin | Vendedor |
|---------|-------|----------|
| Inventario | ✅ | ✅ |
| Ventas | ✅ | ✅ |
| Reportes | ✅ | ❌ |

---

## 📁 Estructura del proyecto
```
Sistema-POS/
├── main.py                  # Punto de entrada
├── config.py                # Configuración global
├── requirements.txt         # Dependencias
├── db/
│   └── database.py          # Conexión y creación de tablas
├── auth/
│   ├── login.py             # Autenticación contra la DB
│   └── session.py           # Manejo de sesión activa
├── modules/
│   ├── inventory.py         # InventoryManager — Dev 2
│   ├── sales.py             # SalesManager — Dev 3
│   └── reports.py           # ReportManager — Dev 4
└── ui/
    ├── login_window.py      # Pantalla de login
    └── main_window.py       # Ventana principal con sidebar
```

---

## 🧩 Contrato de integración

Todos los métodos de los módulos deben retornar siempre este formato:
```python
# Éxito con datos
{"success": True,  "data": <resultado>}

# Éxito sin datos
{"success": True,  "data": None}

# Error
{"success": False, "error": "Descripción del error"}
```

El líder conecta cada módulo a la UI importando directamente:
```python
from modules.inventory import InventoryManager
from modules.sales     import SalesManager
from modules.reports   import ReportManager
```

---

## 🌿 Flujo de trabajo con Git

**1. Antes de arrancar, asegúrate de estar en `dev` actualizado**
```bash
git checkout dev
git pull origin dev
```

**2. Crea tu rama desde `dev`**
```bash
git checkout -b feature/inventario   # Dev 2
git checkout -b feature/ventas       # Dev 3
git checkout -b feature/reportes     # Dev 4
```

**3. Trabaja solo en tu archivo asignado**

| Dev | Archivo |
|-----|---------|
| Dev 2 | `modules/inventory.py` |
| Dev 3 | `modules/sales.py` |
| Dev 4 | `modules/reports.py` |

**4. Haz commits descriptivos mientras avanzas**
```bash
git add .
git commit -m "feat: implementar get_all en InventoryManager"
git push origin feature/inventario
```

**5. Cuando termines abre un Pull Request hacia `dev` en GitHub**
- Ve al repositorio en GitHub
- Clic en **"Compare & pull request"**
- Base: `dev` ← Compare: `feature/tu-rama`
- Describe brevemente qué hiciste
- El líder revisa y aprueba el merge

⚠️ **Nunca hagas push directo a `main`.**