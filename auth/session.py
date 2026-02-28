# Sesión activa del usuario autenticado
current_user = {
    "id": None,
    "nombre": None,
    "usuario": None,
    "rol": None
}


def set_session(user_data):
    current_user["id"]      = user_data["id"]
    current_user["nombre"]  = user_data["nombre"]
    current_user["usuario"] = user_data["usuario"]
    current_user["rol"]     = user_data["rol"]


def get_session():
    return current_user


def clear_session():
    for key in current_user:
        current_user[key] = None


def is_authenticated():
    return current_user["id"] is not None


def is_admin():
    return current_user["rol"] == "admin"