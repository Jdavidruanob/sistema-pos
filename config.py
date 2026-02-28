import os

# Ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta del archivo de base de datos
DB_PATH = os.path.join(BASE_DIR, "db", "pos.db")

# Nombre de la app
APP_NAME = "Mini-Sistema POS"
APP_VERSION = "1.0.0"