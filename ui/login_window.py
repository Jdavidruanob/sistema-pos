from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from auth.login import login


class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini-Sistema POS")
        self.setFixedSize(400, 500)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("background-color: #1F3864;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 60, 50, 60)
        layout.setSpacing(16)

        # Título
        title = QLabel("POS XYZ")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Inicia sesión para continuar")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #A8C4E8; font-size: 13px;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # Campo usuario
        lbl_user = QLabel("Usuario")
        lbl_user.setStyleSheet("color: #A8C4E8; font-size: 13px;")
        layout.addWidget(lbl_user)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Ingresa tu usuario")
        self.input_usuario.setFixedHeight(40)
        self.input_usuario.setStyleSheet("""
            QLineEdit {
                background-color: #2E5FA3;
                border: none;
                border-radius: 6px;
                padding: 0 12px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #A8C4E8;
            }
        """)
        layout.addWidget(self.input_usuario)

        # Campo contraseña
        lbl_pass = QLabel("Contraseña")
        lbl_pass.setStyleSheet("color: #A8C4E8; font-size: 13px;")
        layout.addWidget(lbl_pass)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Ingresa tu contraseña")
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setFixedHeight(40)
        self.input_password.setStyleSheet(self.input_usuario.styleSheet())
        self.input_password.returnPressed.connect(self._handle_login)
        layout.addWidget(self.input_password)

        layout.addSpacing(10)

        # Botón login
        self.btn_login = QPushButton("Ingresar")
        self.btn_login.setFixedHeight(44)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #2E86C1;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover   { background-color: #1A6FA3; }
            QPushButton:pressed { background-color: #145A87; }
        """)
        self.btn_login.clicked.connect(self._handle_login)
        layout.addWidget(self.btn_login)

        layout.addStretch()

        # Label error
        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        self.lbl_error.setStyleSheet("color: #FF6B6B; font-size: 12px;")
        layout.addWidget(self.lbl_error)

    def _handle_login(self):
        usuario  = self.input_usuario.text().strip()
        password = self.input_password.text().strip()

        if not usuario or not password:
            self.lbl_error.setText("Por favor completa todos los campos.")
            return

        resultado = login(usuario, password)

        if resultado["success"]:
            self._abrir_main()
        else:
            self.lbl_error.setText(resultado["error"])
            self.input_password.clear()

    def _abrir_main(self):
        from ui.main_window import MainWindow
        self.main = MainWindow()
        self.main.show()
        self.close()