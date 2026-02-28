from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QVBoxLayout, QPushButton, QStackedWidget, QLabel
)
from PySide6.QtCore import Qt
from auth.session import get_session, clear_session
from auth.session import get_session



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

        # ── Sidebar ──────────────────────────────────────────
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setStyleSheet("background-color: #1F3864;")

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Título en sidebar
        title = QLabel("POS XYZ")
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(60)
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        sidebar_layout.addWidget(title)

        # Botones de navegación
        self.nav_buttons = {}
        nav_items = [
            ("inventario",  "📦  Inventario"),
            ("ventas",      "🛒  Ventas"),
            ("reportes",    "📊  Reportes"),
        ]

        for key, label in nav_items:
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
                QPushButton:hover {
                    background-color: #2E5FA3;
                }
                QPushButton:pressed {
                    background-color: #16407A;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self.navigate(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn

        sidebar_layout.addStretch()

        # Info usuario + cerrar sesión
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

        # ── Panel principal (páginas) ─────────────────────────
        self.stack = QStackedWidget()

        # Páginas vacías — cada dev reemplaza la suya
        self.pages = {
            "inventario": self._placeholder("Módulo de Inventario"),
            "ventas":     self._placeholder("Módulo de Ventas"),
            "reportes":   self._placeholder("Módulo de Reportes"),
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.stack)


        # Ocultar secciones según rol
        if get_session()["rol"] != "admin":
            self.nav_buttons["reportes"].hide()

        # Página inicial
        self.navigate("inventario")

    def _placeholder(self, texto):
        """Página temporal hasta que cada dev conecte su módulo."""
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(texto)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 22px; color: #AAAAAA;")
        layout.addWidget(label)
        return page

    def navigate(self, key):
        self.stack.setCurrentWidget(self.pages[key])
        for k, btn in self.nav_buttons.items():
            btn.setStyleSheet(btn.styleSheet().replace(
                "background-color: #16407A;", "background: transparent;"
            ))

    def logout(self):
        clear_session()
        self.close()