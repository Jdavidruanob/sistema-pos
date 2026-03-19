"""
ui/users_page.py
Módulo completo de Usuarios y Permisos – Dev 1
HU-09 Ver lista | HU-10 Agregar | HU-11 Editar/Activar-Desactivar | HU-12 Gestión de permisos
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QComboBox, QCheckBox, QMessageBox,
    QGroupBox, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from modules.users import (
    get_all_users, create_user, update_user,
    toggle_user_active, delete_user,
    get_permissions, save_all_permissions
)

# Módulos del sistema para el panel de permisos
MODULOS = ["inventario", "ventas", "reportes", "usuarios"]

# ─────────────────────────────────────────────────────────────
# Estilos reutilizables (coherentes con el sidebar #1F3864)
# ─────────────────────────────────────────────────────────────
STYLE_PRIMARY = """
    QPushButton {
        background-color: #1F3864;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #2E5FA3; }
    QPushButton:pressed { background-color: #16407A; }
    QPushButton:disabled { background-color: #AAAAAA; }
"""
STYLE_DANGER = """
    QPushButton {
        background-color: #C0392B;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #E74C3C; }
    QPushButton:pressed { background-color: #A93226; }
"""
STYLE_WARNING = """
    QPushButton {
        background-color: #D4870A;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #E8960E; }
"""
STYLE_SUCCESS = """
    QPushButton {
        background-color: #1E8449;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: bold;
    }
    QPushButton:hover { background-color: #27AE60; }
"""
STYLE_SECONDARY = """
    QPushButton {
        background-color: #566573;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-size: 13px;
    }
    QPushButton:hover { background-color: #717D7E; }
"""


# ═════════════════════════════════════════════════════════════
# Diálogo: Agregar / Editar usuario  (HU-10, HU-11)
# ═════════════════════════════════════════════════════════════
class UserDialog(QDialog):
    """Formulario para crear o editar un usuario."""

    def __init__(self, parent=None, user_data: dict = None):
        super().__init__(parent)
        self.user_data = user_data          # None → modo creación
        self.editing = user_data is not None
        self.setWindowTitle("Editar Usuario" if self.editing else "Nuevo Usuario")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._build_ui()
        if self.editing:
            self._fill_data()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Título
        title = QLabel("Editar Usuario" if self.editing else "Nuevo Usuario")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color: #1F3864;")
        main_layout.addWidget(title)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #D5D8DC;")
        main_layout.addWidget(sep)

        # Formulario
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre completo")
        self.input_nombre.setMinimumHeight(34)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Nombre de usuario (login)")
        self.input_usuario.setMinimumHeight(34)

        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        pwd_hint = "Nueva contraseña (dejar vacío = no cambiar)" if self.editing else "Contraseña"
        self.input_password.setPlaceholderText(pwd_hint)
        self.input_password.setMinimumHeight(34)

        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["vendedor", "admin"])
        self.combo_rol.setMinimumHeight(34)

        input_style = """
            QLineEdit, QComboBox {
                border: 1px solid #AEB6BF;
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 13px;
                background: white;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #2E5FA3; }
        """
        for w in (self.input_nombre, self.input_usuario, self.input_password, self.combo_rol):
            w.setStyleSheet(input_style)

        form.addRow("Nombre:", self.input_nombre)
        form.addRow("Usuario:", self.input_usuario)
        form.addRow("Contraseña:", self.input_password)
        form.addRow("Rol:", self.combo_rol)
        main_layout.addLayout(form)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.setStyleSheet(STYLE_SECONDARY)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Guardar")
        self.btn_save.setStyleSheet(STYLE_PRIMARY)
        self.btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_save)
        main_layout.addLayout(btn_row)

    def _fill_data(self):
        self.input_nombre.setText(self.user_data["nombre"])
        self.input_usuario.setText(self.user_data["usuario"])
        idx = self.combo_rol.findText(self.user_data["rol"])
        if idx >= 0:
            self.combo_rol.setCurrentIndex(idx)

    def _on_save(self):
        nombre   = self.input_nombre.text().strip()
        usuario  = self.input_usuario.text().strip()
        password = self.input_password.text()
        rol      = self.combo_rol.currentText()
 
        if not nombre or not usuario:
            QMessageBox.warning(self, "Campos incompletos",
                                "Nombre y usuario son obligatorios.")
            return
        if not self.editing and not password:
            QMessageBox.warning(self, "Contraseña requerida",
                                "Debes ingresar una contraseña para el nuevo usuario.")
            return
 
        if self.editing:
            result = update_user(
                self.user_data["id"], nombre, usuario, rol,
                password if password else None
            )
        else:
            result = create_user(nombre, usuario, password, rol)
 
            # Al crear, asignar permisos por defecto según rol
            if result["success"]:
                from modules.users import save_all_permissions, get_all_users
                from db.database import get_connection
 
                # Obtener el ID del usuario recién creado
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
                row = cursor.fetchone()
                conn.close()
 
                if row:
                    new_id = row["id"]
                    if rol == "admin":
                        # Admin obtiene todos los módulos
                        perms = {m: True for m in ["dashboard", "usuarios", "inventario", "ventas", "reportes"]}
                    else:
                        # Vendedor: inventario y ventas por defecto
                        perms = {
                            "dashboard":  False,
                            "usuarios":   False,
                            "inventario": True,
                            "ventas":     True,
                            "reportes":   False,
                        }
                    save_all_permissions(new_id, perms)
 
        if result["success"]:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", result["error"])


# ═════════════════════════════════════════════════════════════
# Diálogo: Gestión de permisos  (HU-12)
# ═════════════════════════════════════════════════════════════
class PermissionsDialog(QDialog):
    """Permite activar/desactivar módulos para un usuario."""

    def __init__(self, parent=None, user_data: dict = None):
        super().__init__(parent)
        self.user_data = user_data
        self.setWindowTitle(f"Permisos — {user_data['nombre']}")
        self.setMinimumWidth(380)
        self.setModal(True)
        self.checks = {}
        self._build_ui()
        self._load_permissions()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Título
        title = QLabel(f"Permisos de módulos")
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color: #1F3864;")
        main_layout.addWidget(title)

        sub = QLabel(f"Usuario: {self.user_data['nombre']}  |  Rol: {self.user_data['rol']}")
        sub.setStyleSheet("color: #566573; font-size: 12px;")
        main_layout.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #D5D8DC;")
        main_layout.addWidget(sep)

        # Checkboxes por módulo
        group = QGroupBox("Acceso a módulos")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 13px; font-weight: bold;
                border: 1px solid #AEB6BF;
                border-radius: 6px;
                padding: 12px;
                margin-top: 8px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
        """)
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(10)

        for modulo in MODULOS:
            cb = QCheckBox(modulo.capitalize())
            cb.setStyleSheet("font-size: 13px;")
            group_layout.addWidget(cb)
            self.checks[modulo] = cb

        main_layout.addWidget(group)

        # Nota informativa
        note = QLabel("ℹ️  Los admins tienen acceso completo por defecto.")
        note.setStyleSheet("color: #808B96; font-size: 11px; font-style: italic;")
        note.setWordWrap(True)
        main_layout.addWidget(note)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet(STYLE_SECONDARY)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Guardar permisos")
        btn_save.setStyleSheet(STYLE_PRIMARY)
        btn_save.clicked.connect(self._on_save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        main_layout.addLayout(btn_row)

    def _load_permissions(self):
        perms = get_permissions(self.user_data["id"])
        for modulo, cb in self.checks.items():
            # Si no tiene registro, vendedor=False para reportes/usuarios, True para el resto
            default = True if modulo in ("inventario", "ventas") else False
            cb.setChecked(perms.get(modulo, default))

    def _on_save(self):
        perms = {modulo: cb.isChecked() for modulo, cb in self.checks.items()}
        result = save_all_permissions(self.user_data["id"], perms)
        if result["success"]:
            QMessageBox.information(self, "Éxito", "Permisos actualizados correctamente.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", result["error"])


# ═════════════════════════════════════════════════════════════
# Página principal: lista de usuarios  (HU-09)
# ═════════════════════════════════════════════════════════════
class UsersPage(QWidget):
    """Página completa del módulo de Usuarios y Permisos."""

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # ── Cabecera ──────────────────────────────────────────
        header = QHBoxLayout()

        title = QLabel("👥  Usuarios y Permisos")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #1F3864;")
        header.addWidget(title)
        header.addStretch()

        self.btn_refresh = QPushButton("↻  Actualizar")
        self.btn_refresh.setStyleSheet(STYLE_SECONDARY)
        self.btn_refresh.clicked.connect(self.load_users)

        self.btn_new = QPushButton("＋  Nuevo usuario")
        self.btn_new.setStyleSheet(STYLE_PRIMARY)
        self.btn_new.clicked.connect(self._on_new_user)

        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_new)
        layout.addLayout(header)

        # ── Tabla ─────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Usuario", "Rol", "Estado", "Acciones"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #D5D8DC;
                border-radius: 8px;
                font-size: 13px;
                gridline-color: #EBF0F1;
            }
            QHeaderView::section {
                background-color: #1F3864;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 8px;
                border: none;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected {
                background-color: #D6E4F0;
                color: #1F3864;
            }
        """)

        layout.addWidget(self.table)

        # Carga inicial
        self.load_users()

    # ── Carga / refresco de datos ─────────────────────────────
    def load_users(self):
        users = get_all_users()
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            # Celdas de datos
            self.table.setItem(row, 0, self._cell(str(user["id"]), center=True))
            self.table.setItem(row, 1, self._cell(user["nombre"]))
            self.table.setItem(row, 2, self._cell(user["usuario"]))

            # Rol con color
            rol_item = self._cell(user["rol"].capitalize(), center=True)
            if user["rol"] == "admin":
                rol_item.setForeground(QColor("#1F3864"))
                rol_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table.setItem(row, 3, rol_item)

            # Estado (badge)
            estado_item = self._cell(
                "✅ Activo" if user["activo"] else "🔴 Inactivo",
                center=True
            )
            estado_item.setForeground(
                QColor("#1E8449") if user["activo"] else QColor("#C0392B")
            )
            self.table.setItem(row, 4, estado_item)

            # Botones de acción
            actions_widget = self._make_action_buttons(user)
            self.table.setCellWidget(row, 5, actions_widget)
            self.table.setRowHeight(row, 48)

        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 100)

    def _cell(self, text, center=False):
        item = QTableWidgetItem(text)
        if center:
            item.setTextAlignment(Qt.AlignCenter)
        return item

    def _make_action_buttons(self, user: dict) -> QWidget:
        """Crea el widget con botones Editar / Activar-Desactivar / Permisos / Eliminar."""
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(6, 4, 6, 4)
        row_layout.setSpacing(6)

        # Editar (HU-11)
        btn_edit = QPushButton("✏️")
        btn_edit.setToolTip("Editar usuario")
        btn_edit.setFixedSize(34, 34)
        btn_edit.setStyleSheet(STYLE_PRIMARY)
        btn_edit.clicked.connect(lambda _, u=user: self._on_edit_user(u))

        # Activar / Desactivar (HU-11)
        if user["activo"]:
            btn_toggle = QPushButton("🔴")
            btn_toggle.setToolTip("Desactivar usuario")
            btn_toggle.setStyleSheet(STYLE_WARNING)
        else:
            btn_toggle = QPushButton("✅")
            btn_toggle.setToolTip("Activar usuario")
            btn_toggle.setStyleSheet(STYLE_SUCCESS)
        btn_toggle.setFixedSize(34, 34)
        btn_toggle.clicked.connect(lambda _, u=user: self._on_toggle(u))

        # Permisos (HU-12)
        btn_perms = QPushButton("🔑")
        btn_perms.setToolTip("Gestionar permisos")
        btn_perms.setFixedSize(34, 34)
        btn_perms.setStyleSheet(STYLE_SECONDARY)
        btn_perms.clicked.connect(lambda _, u=user: self._on_permissions(u))

        # Eliminar
        btn_del = QPushButton("🗑️")
        btn_del.setToolTip("Eliminar usuario")
        btn_del.setFixedSize(34, 34)
        btn_del.setStyleSheet(STYLE_DANGER)
        btn_del.clicked.connect(lambda _, u=user: self._on_delete(u))

        row_layout.addWidget(btn_edit)
        row_layout.addWidget(btn_toggle)
        row_layout.addWidget(btn_perms)
        row_layout.addWidget(btn_del)
        return container

    # ── Handlers ─────────────────────────────────────────────
    def _on_new_user(self):
        dlg = UserDialog(parent=self)
        if dlg.exec():
            self.load_users()

    def _on_edit_user(self, user: dict):
        dlg = UserDialog(parent=self, user_data=user)
        if dlg.exec():
            self.load_users()

    def _on_toggle(self, user: dict):
        accion = "desactivar" if user["activo"] else "activar"
        resp = QMessageBox.question(
            self, "Confirmar",
            f"¿Deseas {accion} al usuario '{user['nombre']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            result = toggle_user_active(user["id"], user["activo"])
            if result["success"]:
                self.load_users()
            else:
                QMessageBox.critical(self, "Error", result["error"])

    def _on_permissions(self, user: dict):
        if user["rol"] == "admin":
            QMessageBox.information(
                self,
                "Permisos de administrador",
                f"'{user['nombre']}' es administrador y tiene acceso completo a todos los módulos del sistema.\n\n"
                "Los permisos personalizados solo aplican a usuarios con rol vendedor."
            )
            return
        dlg = PermissionsDialog(parent=self, user_data=user)
        if dlg.exec():
            self.load_users()

    def _on_delete(self, user: dict):
        resp = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Seguro que deseas eliminar a '{user['nombre']}'?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            result = delete_user(user["id"])
            if result["success"]:
                QMessageBox.information(self, "Éxito", "Usuario eliminado.")
                self.load_users()
            else:
                QMessageBox.critical(self, "Error", result["error"])