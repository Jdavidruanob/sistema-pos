from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QStackedWidget, QLabel
)
from PySide6.QtCore import Qt
from auth.session import get_session, clear_session
from ui.inventory_page import InventoryPage
from ui.sales_page import SalesPage
from ui.reports_page import ReportsPage
from ui.users_page import UsersPage
from ui.dashboard_page import DashboardPage
from modules.users import get_permissions


# Módulos disponibles en el orden del sidebar
NAV_ITEMS = [
    ("dashboard",  "📊  Dashboard"),
    ("usuarios",   "👥  Usuarios"),
    ("inventario", "📦  Inventario"),
    ("ventas",     "🛒  Ventas"),
    ("reportes",   "📈  Reportes"),
]

# Módulos que el admin siempre tiene sin importar permisos
ADMIN_ALWAYS = {"dashboard", "usuarios", "inventario", "ventas", "reportes"}


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini-Sistema POS")
        self.setMinimumSize(1000, 650)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #1F3864;")

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        title = QLabel("POS XYZ")
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(60)
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        sidebar_layout.addWidget(title)

        self.nav_buttons = {}
        for key, label in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setFixedHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    color: white;
                    background: transparent;
                    border: none;
                    font-size: 14px;
                    text-align: left;
                    padding-left: 24px;
                }
                QPushButton:hover   { background-color: #2E5FA3; }
                QPushButton:pressed { background-color: #16407A; }
            """)
            btn.clicked.connect(lambda checked, k=key: self.navigate(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        sidebar_layout.addStretch()

        session = get_session()
        self.user_label = QLabel(f"👤  {session['nombre'] or 'Usuario'}")
        self.user_label.setAlignment(Qt.AlignCenter)
        self.user_label.setStyleSheet("color: #A8C4E8; font-size: 12px;")
        self.user_label.setFixedHeight(30)
        sidebar_layout.addWidget(self.user_label)

        btn_logout = QPushButton("Cerrar sesión")
        btn_logout.setFixedHeight(40)
        btn_logout.setStyleSheet("""
            QPushButton {
                color: #A8C4E8;
                background: transparent;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { color: white; }
        """)
        btn_logout.clicked.connect(self.logout)
        sidebar_layout.addWidget(btn_logout)

        # ── Panel principal ────────────────────────────────────
        self.stack = QStackedWidget()

        self.pages = {
            "dashboard":  DashboardPage(),
            "usuarios":   UsersPage(),
            "inventario": InventoryPage(),
            "ventas":     SalesPage(),
            "reportes":   ReportsPage(),
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.stack)

        # ── Aplicar permisos al sidebar ────────────────────────
        self._apply_permissions()

        # ── Página inicial ─────────────────────────────────────
        primera = self._first_allowed_page()
        if primera:
            self.navigate(primera)

    def _apply_permissions(self):
        """
        Muestra u oculta botones del sidebar según rol y permisos.
        - Admin: siempre ve todo, sin consultar la tabla permisos.
        - Otros: se consulta la tabla permisos en la DB.
          Si un módulo no tiene registro en permisos, se asume NO permitido.
        """
        session = get_session()

        if session["rol"] == "admin":
            # Admin ve todo, nada que ocultar
            for btn in self.nav_buttons.values():
                btn.show()
            return

        # Leer permisos reales de la DB para este usuario
        perms = get_permissions(session["id"])
        # perms = {"inventario": True, "ventas": True, ...}

        for key, btn in self.nav_buttons.items():
            # Si el módulo tiene permiso True → mostrar, si no → ocultar
            if perms.get(key, False):
                btn.show()
            else:
                btn.hide()

    def _first_allowed_page(self):
        """Retorna la primera página visible para navegar al inicio."""
        for key, _ in NAV_ITEMS:
            if self.nav_buttons[key].isVisible():
                return key
        return None

    def navigate(self, key):
        # Seguridad: no navegar a páginas ocultas
        if not self.nav_buttons[key].isVisible():
            return
        page = self.pages[key]
        self.stack.setCurrentWidget(page)
        if hasattr(page, "on_activated"):
            page.on_activated()

    def logout(self):
        from ui.login_window import LoginWindow
        clear_session()
        self.login = LoginWindow()
        self.login.show()
        self.close()
