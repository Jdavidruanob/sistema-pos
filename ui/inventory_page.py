from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QDialog, QFormLayout,
    QDoubleSpinBox, QSpinBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from modules.inventory import InventoryManager

BTN_PRIMARY = """
    QPushButton {
        background-color: #2E86C1; color: white;
        border: none; border-radius: 6px;
        font-size: 13px; font-weight: bold; padding: 8px 16px;
    }
    QPushButton:hover   { background-color: #1A6FA3; }
    QPushButton:pressed { background-color: #145A87; }
"""
BTN_DANGER = """
    QPushButton {
        background-color: #C0392B; color: white;
        border: none; border-radius: 4px;
        font-size: 12px; padding: 4px 10px;
    }
    QPushButton:hover { background-color: #A93226; }
"""
BTN_WARNING = """
    QPushButton {
        background-color: #D4AC0D; color: white;
        border: none; border-radius: 4px;
        font-size: 12px; padding: 4px 10px;
    }
    QPushButton:hover { background-color: #B7950B; }
"""
TBL_STYLE = """
    QTableWidget {
        border: 1px solid #D5D8DC;
        border-radius: 6px;
        gridline-color: #EBF0F0;
        font-size: 13px;
    }
    QHeaderView::section {
        background-color: #1F3864;
        color: white; padding: 6px;
        border: none; font-size: 13px; font-weight: bold;
    }
    QTableWidget::item:selected { background-color: #D6EAF8; color: black; }
"""


class InventoryPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = InventoryManager()
        self._all_products = []
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Encabezado
        header = QHBoxLayout()
        title = QLabel("📦  Inventario de Productos")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F3864;")
        header.addWidget(title)
        header.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Buscar producto...")
        self.search.setFixedHeight(34)
        self.search.setFixedWidth(220)
        self.search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #AEB6BF; border-radius: 6px;
                padding: 0 10px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #2E86C1; }
        """)
        self.search.textChanged.connect(self._filter)
        header.addWidget(self.search)

        btn_add = QPushButton("➕  Agregar producto")
        btn_add.setStyleSheet(BTN_PRIMARY)
        btn_add.clicked.connect(self._open_add_dialog)
        header.addWidget(btn_add)
        root.addLayout(header)

        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Categoría", "Precio", "Stock", "Descuento", "Editar", "Eliminar"]
        )
        self.table.setStyleSheet(TBL_STYLE)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 40)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 60)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 70)
        self.table.setColumnWidth(7, 70)
        root.addWidget(self.table)

    def _load(self):
        result = self._manager.get_all()
        if result["success"]:
            self._all_products = result["data"]
            self._render(self._all_products)
        else:
            QMessageBox.warning(self, "Error", result["error"])

    def _render(self, products):
        self.table.setRowCount(0)
        for p in products:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, self._cell(str(p["id"]), Qt.AlignCenter))
            self.table.setItem(row, 1, self._cell(p["nombre"]))
            self.table.setItem(row, 2, self._cell(p["categoria"] or "—", Qt.AlignCenter))
            self.table.setItem(row, 3, self._cell(f"$ {p['precio']:,.0f}", Qt.AlignRight))
            self.table.setItem(row, 4, self._cell(str(p["cantidad"]), Qt.AlignCenter))
            
            # Columna de descuento
            descuento_pct = p.get("descuento_pct", 0)
            descuento_activo = p.get("descuento_activo", 0)
            if descuento_activo and descuento_pct > 0:
                descuento_text = f"🎁 {descuento_pct:.0f}%"
                descuento_item = self._cell(descuento_text, Qt.AlignCenter)
                from PySide6.QtGui import QColor, QFont
                descuento_item.setForeground(QColor("#1E8449"))
                font = descuento_item.font()
                font.setBold(True)
                descuento_item.setFont(font)
                self.table.setItem(row, 5, descuento_item)
            else:
                self.table.setItem(row, 5, self._cell("Sin descuento", Qt.AlignCenter))
            
            btn_discount = QPushButton("🎁 Descuento")
            btn_discount.setStyleSheet(BTN_WARNING)
            btn_discount.clicked.connect(lambda _, pid=p["id"]: self._open_discount_dialog(pid))
            self.table.setCellWidget(row, 5, btn_discount)

            btn_edit = QPushButton("✏️ Editar")
            btn_edit.setStyleSheet(BTN_WARNING)
            btn_edit.clicked.connect(lambda _, pid=p["id"]: self._open_edit_dialog(pid))
            self.table.setCellWidget(row, 6, btn_edit)

            btn_del = QPushButton("🗑 Eliminar")
            btn_del.setStyleSheet(BTN_DANGER)
            btn_del.clicked.connect(lambda _, pid=p["id"], nom=p["nombre"]: self._delete(pid, nom))
            self.table.setCellWidget(row, 7, btn_del)

    def _filter(self, text):
        text = text.lower().strip()
        if not text:
            self._render(self._all_products)
            return
        filtered = [
            p for p in self._all_products
            if text in p["nombre"].lower()
            or text in (p["categoria"] or "").lower()
        ]
        self._render(filtered)

    def _open_add_dialog(self):
        dlg = ProductDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            result = self._manager.add(
                data["nombre"], data["precio"], data["cantidad"], data["categoria"]
            )
            if result["success"]:
                self._load()
            else:
                QMessageBox.critical(self, "Error", result["error"])

    def _open_edit_dialog(self, producto_id):
        result = self._manager.get_by_id(producto_id)
        if not result["success"]:
            QMessageBox.warning(self, "Error", result["error"])
            return
        dlg = ProductDialog(self, data=result["data"])
        if dlg.exec():
            data = dlg.get_data()
            res = self._manager.update(
                producto_id, data["nombre"], data["precio"],
                data["cantidad"], data["categoria"]
            )
            if res["success"]:
                self._load()
            else:
                QMessageBox.critical(self, "Error", res["error"])

    def _delete(self, producto_id, nombre):
        resp = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Eliminar '{nombre}' del inventario?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            result = self._manager.delete(producto_id)
            if result["success"]:
                self._load()
            else:
                QMessageBox.critical(self, "Error", result["error"])

    def _open_discount_dialog(self, producto_id):
        result = self._manager.get_by_id(producto_id)
        if not result["success"]:
            QMessageBox.warning(self, "Error", result["error"])
            return
        
        dlg = DiscountDialog(self, data=result["data"])
        if dlg.exec():
            descuento_pct = dlg.get_discount_pct()
            descuento_activo = dlg.get_discount_active()
            res = self._manager.set_discount(producto_id, descuento_pct, descuento_activo)
            if res["success"]:
                self._load()
            else:
                QMessageBox.critical(self, "Error", res["error"])

    @staticmethod
    def _cell(text, alignment=Qt.AlignLeft | Qt.AlignVCenter):
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        return item


class ProductDialog(QDialog):
    """Diálogo para agregar o editar un producto."""

    CATEGORIAS = ["Bebidas", "Snacks", "Lácteos", "Panadería", "Platos", "Otros"]

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self._data = data
        self.setWindowTitle("Agregar producto" if not data else "Editar producto")
        self.setFixedWidth(380)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.input_nombre = QLineEdit()
        self.input_nombre.setFixedHeight(34)
        self.input_nombre.setStyleSheet("border:1px solid #AEB6BF; border-radius:5px; padding:0 8px; font-size:13px;")

        self.input_categoria = QComboBox()
        self.input_categoria.addItems(self.CATEGORIAS)
        self.input_categoria.setFixedHeight(34)

        self.input_precio = QDoubleSpinBox()
        self.input_precio.setRange(0, 9999999)
        self.input_precio.setDecimals(0)
        self.input_precio.setPrefix("$ ")
        self.input_precio.setFixedHeight(34)
        self.input_precio.setStyleSheet("font-size:13px;")

        self.input_cantidad = QSpinBox()
        self.input_cantidad.setRange(0, 99999)
        self.input_cantidad.setFixedHeight(34)
        self.input_cantidad.setStyleSheet("font-size:13px;")

        form.addRow("Nombre:", self.input_nombre)
        form.addRow("Categoría:", self.input_categoria)
        form.addRow("Precio:", self.input_precio)
        form.addRow("Cantidad:", self.input_cantidad)
        layout.addLayout(form)

        # Pre-llenar si es edición
        if self._data:
            self.input_nombre.setText(self._data["nombre"])
            idx = self.input_categoria.findText(self._data.get("categoria") or "")
            if idx >= 0:
                self.input_categoria.setCurrentIndex(idx)
            self.input_precio.setValue(self._data["precio"])
            self.input_cantidad.setValue(self._data["cantidad"])

        # Botones
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setFixedHeight(36)
        btn_save.setStyleSheet(BTN_PRIMARY)
        btn_save.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _validate_and_accept(self):
        if not self.input_nombre.text().strip():
            QMessageBox.warning(self, "Campo requerido", "El nombre del producto es obligatorio.")
            return
        self.accept()

    def get_data(self):
        return {
            "nombre":    self.input_nombre.text().strip(),
            "categoria": self.input_categoria.currentText(),
            "precio":    self.input_precio.value(),
            "cantidad":  self.input_cantidad.value(),
        }


class DiscountDialog(QDialog):
    """Diálogo para configurar descuentos en un producto."""

    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self._data = data
        self._activo = 0
        self.setWindowTitle("Configurar Descuento")
        self.setFixedWidth(340)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Nombre del producto (para referencia)
        if self._data:
            lbl_nombre = QLabel(f"Producto: {self._data['nombre']}")
            lbl_nombre.setStyleSheet("font-size:13px; font-weight:bold; color:#1F3864;")
            layout.addWidget(lbl_nombre)

        form = QFormLayout()
        form.setSpacing(12)

        # Porcentaje de descuento
        self.input_descuento = QDoubleSpinBox()
        self.input_descuento.setRange(0, 100)
        self.input_descuento.setDecimals(1)
        self.input_descuento.setSuffix(" %")
        self.input_descuento.setFixedHeight(34)
        self.input_descuento.setStyleSheet("font-size:13px;")
        self.input_descuento.valueChanged.connect(self._update_button_state)
        form.addRow("Descuento (%):", self.input_descuento)

        # Checkbox para activar/desactivar
        self.check_activo = QLineEdit()
        self.check_activo.setFixedHeight(34)
        self.check_activo.setReadOnly(True)
        self.check_activo.setStyleSheet("font-size:13px;")
        
        # Mejor usamos dos botones en lugar de checkbox
        layout.addLayout(form)
        
        btn_row = QHBoxLayout()
        self.btn_toggle = QPushButton("Activar descuento")
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #1E8449; color: white;
                border: none; border-radius: 6px;
                font-size: 13px; font-weight: bold; padding: 8px 16px;
            }
            QPushButton:hover   { background-color: #196F3D; }
            QPushButton:pressed { background-color: #145A32; }
        """)
        self.btn_toggle.setFixedHeight(36)
        self.btn_toggle.clicked.connect(self._toggle_active)
        btn_row.addWidget(self.btn_toggle)
        
        layout.addLayout(btn_row)

        # Pre-llenar si es edición
        if self._data:
            self.input_descuento.setValue(self._data.get("descuento_pct", 0))
            self._activo = self._data.get("descuento_activo", 0) == 1
            self._update_button_state()

        # Botones del diálogo
        btn_row_dialog = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setFixedHeight(36)
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setFixedHeight(36)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2E86C1; color: white;
                border: none; border-radius: 6px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover   { background-color: #1A6FA3; }
            QPushButton:pressed { background-color: #145A87; }
        """)
        btn_save.clicked.connect(self.accept)
        btn_row_dialog.addWidget(btn_cancel)
        btn_row_dialog.addWidget(btn_save)
        layout.addLayout(btn_row_dialog)

    def _toggle_active(self):
        self._activo = not self._activo
        self._update_button_state()

    def _update_button_state(self):
        if self._activo:
            self.btn_toggle.setText(f"✅ Descuento activo ({self.input_descuento.value():.1f}%)")
            self.btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #1E8449; color: white;
                    border: none; border-radius: 6px;
                    font-size: 13px; font-weight: bold; padding: 8px 16px;
                }
            """)
        else:
            self.btn_toggle.setText("Descuento desactivado")
            self.btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #95A5A6; color: white;
                    border: none; border-radius: 6px;
                    font-size: 13px; font-weight: bold; padding: 8px 16px;
                }
            """)

    def get_discount_pct(self):
        return self.input_descuento.value()

    def get_discount_active(self):
        return 1 if self._activo else 0