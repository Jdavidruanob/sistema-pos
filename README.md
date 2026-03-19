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

## 🔐 Roles y permisos

A partir del Sprint 2 los permisos de cada usuario se gestionan directamente desde la app. El administrador puede configurar qué módulos del sidebar puede ver cada usuario al crearlo o editarlo.

Por defecto:

| Sección | Admin | Vendedor |
|---------|-------|----------|
| Inventario | ✅ | ❌ |
| Ventas | ✅ | ✅ |
| Reportes | ✅ | ✅ |
| Dashboard | ✅ | ❌ |
| Usuarios | ✅ | ❌ |

> Los permisos pueden modificarse por usuario desde el módulo de Usuarios.

---

## 📦 Agregar nuevas dependencias

Si durante el desarrollo instalas una librería nueva, **debes actualizarla en `requirements.txt`** antes de hacer commit para que todos los demás puedan instalarla.

```bash
# 1. Instala la librería
pip install nombre-libreria

# 2. Actualiza requirements.txt
pip freeze > requirements.txt

# 3. Incluye el requirements.txt en tu commit
git add requirements.txt
git commit -m "chore: agregar nombre-libreria a requirements"
```

> ⚠️ No hagas `pip freeze` si tienes otras librerías de prueba instaladas que no son parte del proyecto. Instala solo lo necesario dentro del venv del proyecto.

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

---

## 🌿 Flujo de trabajo con Git

**1. Antes de arrancar, asegúrate de estar en `dev` actualizado**
```bash
git checkout dev
git pull origin dev
```

**2. Crea tu rama desde `dev`**
```bash
git checkout -b feature/usuarios      # Dev 1
git checkout -b feature/dashboard     # Dev 2
git checkout -b feature/descuentos    # Dev 3
git checkout -b feature/reporte-diario # Dev 4
```

**3. Trabaja solo en tus archivos asignados**

| Dev | Sprint 1 | Sprint 2 |
|-----|----------|----------|
| Dev 1 | `auth/login.py`, `auth/session.py` | `modules/users.py`, `ui/users_page.py` |
| Dev 2 | `modules/inventory.py`, `ui/inventory_page.py` | `modules/dashboard.py`, `ui/dashboard_page.py` |
| Dev 3 | `modules/sales.py`, `ui/sales_page.py` | `modules/discounts.py`, modificaciones en `ui/sales_page.py` y `ui/inventory_page.py` |
| Dev 4 | `modules/reports.py`, `ui/reports_page.py` | `modules/export.py`, modificaciones en `ui/reports_page.py` |

**4. Haz commits descriptivos mientras avanzas**
```bash
git add .
git commit -m "feat: implementar lista de usuarios con permisos"
git push origin feature/usuarios
```

**5. Cuando termines abre un Pull Request hacia `dev` en GitHub**
- Ve al repositorio en GitHub
- Clic en **"Compare & pull request"**
- Base: `dev` ← Compare: `feature/tu-rama`
- Describe brevemente qué hiciste y qué archivos modificaste
- El líder revisa y aprueba el merge

⚠️ **Nunca hagas push directo a `main`.**

---

## 📌 Notas importantes Sprint 2

- **Dev 1** debe exponer un método en `UsersManager` para consultar los permisos de un usuario por ID, ya que el `MainWindow` lo usará para construir el sidebar dinámicamente al iniciar sesión.
- **Dev 3** agrega el botón de descuento directamente en `ui/inventory_page.py`. Coordina con Dev 2 del Sprint 1 antes de modificar ese archivo para evitar conflictos.
- **Dev 2** (Dashboard) solo lee datos de ventas e inventario existentes. No modifica ninguna tabla ni módulo del Sprint 1.
- **Dev 4** (Reporte diario) solo lee datos de ventas. No modifica tablas existentes.