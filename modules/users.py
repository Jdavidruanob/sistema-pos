from db.database import get_connection


# ──────────────────────────────────────────────
#  USUARIOS
# ──────────────────────────────────────────────

def get_all_users():
    """Retorna todos los usuarios registrados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, usuario, rol, activo
        FROM usuarios
        ORDER BY nombre
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def get_user_by_id(user_id):
    """Retorna un usuario por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, usuario, rol, activo
        FROM usuarios WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(nombre, usuario, password, rol):
    """Crea un nuevo usuario. Retorna {'success': bool, 'error': str}."""
    if not nombre.strip() or not usuario.strip() or not password.strip():
        return {"success": False, "error": "Todos los campos son obligatorios."}
    if rol not in ("admin", "vendedor"):
        return {"success": False, "error": "Rol inválido."}
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre, usuario, password, rol, activo)
            VALUES (?, ?, ?, ?, 1)
        """, (nombre.strip(), usuario.strip(), password, rol))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        if "UNIQUE" in str(e):
            return {"success": False, "error": f"El nombre de usuario '{usuario}' ya existe."}
        return {"success": False, "error": str(e)}


def update_user(user_id, nombre, usuario, rol, password=None):
    """Actualiza datos de un usuario. Si password es None, no la cambia."""
    if not nombre.strip() or not usuario.strip():
        return {"success": False, "error": "Nombre y usuario son obligatorios."}
    if rol not in ("admin", "vendedor"):
        return {"success": False, "error": "Rol inválido."}
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if password:
            cursor.execute("""
                UPDATE usuarios
                SET nombre = ?, usuario = ?, rol = ?, password = ?
                WHERE id = ?
            """, (nombre.strip(), usuario.strip(), rol, password, user_id))
        else:
            cursor.execute("""
                UPDATE usuarios
                SET nombre = ?, usuario = ?, rol = ?
                WHERE id = ?
            """, (nombre.strip(), usuario.strip(), rol, user_id))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        if "UNIQUE" in str(e):
            return {"success": False, "error": f"El nombre de usuario '{usuario}' ya existe."}
        return {"success": False, "error": str(e)}


def toggle_user_active(user_id, current_state):
    """Activa o desactiva un usuario."""
    new_state = 0 if current_state else 1
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE usuarios SET activo = ? WHERE id = ?",
            (new_state, user_id)
        )
        conn.commit()
        conn.close()
        return {"success": True, "activo": new_state}
    except Exception as e:
        return {"success": False, "error": str(e)}


def delete_user(user_id):
    """Elimina un usuario por ID (solo si no tiene ventas asociadas)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM ventas WHERE vendedor_id = ?", (user_id,)
        )
        if cursor.fetchone()[0] > 0:
            conn.close()
            return {
                "success": False,
                "error": "No se puede eliminar: el usuario tiene ventas registradas.\n"
                         "Puedes desactivarlo en su lugar."
            }
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ──────────────────────────────────────────────
#  PERMISOS  (tabla permisos)
# ──────────────────────────────────────────────

def get_permissions(user_id):
    """Retorna los permisos del usuario como dict {modulo: bool}."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT modulo, permitido FROM permisos WHERE usuario_id = ?",
        (user_id,)
    )
    perms = {row["modulo"]: bool(row["permitido"]) for row in cursor.fetchall()}
    conn.close()
    return perms


def set_permission(user_id, modulo, permitido: bool):
    """Inserta o actualiza un permiso específico."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO permisos (usuario_id, modulo, permitido)
            VALUES (?, ?, ?)
            ON CONFLICT(usuario_id, modulo)
            DO UPDATE SET permitido = excluded.permitido
        """, (user_id, modulo, 1 if permitido else 0))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_all_permissions(user_id, perms: dict):
    """Guarda todos los permisos de un usuario de una vez. perms = {modulo: bool}."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for modulo, permitido in perms.items():
            cursor.execute("""
                INSERT INTO permisos (usuario_id, modulo, permitido)
                VALUES (?, ?, ?)
                ON CONFLICT(usuario_id, modulo)
                DO UPDATE SET permitido = excluded.permitido
            """, (user_id, modulo, 1 if permitido else 0))
        conn.commit()
        conn.close()
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}