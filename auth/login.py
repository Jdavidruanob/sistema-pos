import sqlite3
from db.database import get_connection
from auth.session import set_session


def login(usuario, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nombre, usuario, rol
            FROM usuarios
            WHERE usuario = ? AND password = ? AND activo = 1
        """, (usuario, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            set_session({
                "id":      user["id"],
                "nombre":  user["nombre"],
                "usuario": user["usuario"],
                "rol":     user["rol"]
            })
            return {"success": True, "data": dict(user)}
        else:
            return {"success": False, "error": "Usuario o contraseña incorrectos"}

    except Exception as e:
        return {"success": False, "error": str(e)}