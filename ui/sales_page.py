from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QMessageBox, QDialog, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from modules.inventory import InventoryManager
from modules.sales import SalesManager
from auth.session import get_session


# ── Estilos compartidos ───────────────────────────────────────────────────────
BTN_PRIMARY = """
    QPushButton {
        background-color: #2E86C1; color: white;
        border: none; border-radius: 6px;
        font-size: 13px; font-weight: bold; padding: 8px 16px;
    }
    QPushButton:hover   { background-color: #1A6FA3; }
    QPushButton:pressed { background-color: #145A87; }
    QPushButton:disabled { background-color: #AAAAAA; }
"""
BTN_SUCCESS = """
    QPushButton {
        background-color: #1E8449; color: white;
        border: none; border-radius: 6px;
        font-size: 14px; font-weight: bold; padding: 10px 20px;
    }
    QPushButton:hover   { background-color: #196F3D; }
    QPushButton:pressed { background-color: #145A32; }
    QPushButton:disabled { background-color: #AAAAAA; }
"""
BTN_DANGER = """
    QPushButton {
        background-color: #C0392B; color: white;
        border: none; border-radius: 4px;
        font-size: 12px; padding: 4px 10px;
    }
    QPushButton:hover { background-color: #A93226; }
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
        color: white;
        padding: 6px;
        border: none;
        font-size: 13px;
        font-weight: bold;
    }
    QTableWidget::item:selected {
        background-color: #D6EAF8;
        color: black;
    }
"""


class SalesPage(QWidget):
    """Página principal del módulo de Ventas (HU-07)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._inv = InventoryManager()
        self._sales = SalesManager()
        # carrito: lista de dicts con keys producto_id, nombre, precio_unit, cantidad, stock
        self._cart: list[dict] = []
        self._all_products: list[dict] = []
        self._build_ui()
        self._load_products()

    # ── Construcción de la UI ────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # Encabezado
        title = QLabel("🛒  Registrar Venta")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F3864;")
        root.addWidget(title)

        # Cuerpo: dos columnas
        body = QHBoxLayout()
        body.setSpacing(20)
        root.addLayout(body)

        body.addLayout(self._build_left_panel(), stretch=3)
        body.addLayout(self._build_right_panel(), stretch=2)

    def _build_left_panel(self):
        """Panel izquierdo: búsqueda + tabla de productos disponibles."""
        layout = QVBoxLayout()
        layout.setSpacing(8)

        lbl = QLabel("Productos disponibles")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1F3864;")
        layout.addWidget(lbl)

        # Barra de búsqueda
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Buscar por nombre o categoría...")
        self.search_input.setFixedHeight(36)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #AEB6BF;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 13px;
            }
            QLineEdit:focus { border-color: #2E86C1; }
        """)
        self.search_input.textChanged.connect(self._filter_products)
        layout.addWidget(self.search_input)

        # Tabla de productos
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Categoría", "Precio", "Stock"]
        )
        self.product_table.setStyleSheet(TBL_STYLE)
        self.product_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.product_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.product_table.setAlternatingRowColors(True)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.product_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.product_table.setColumnWidth(0, 40)
        self.product_table.setColumnWidth(3, 90)
        self.product_table.setColumnWidth(4, 60)
        self.product_table.doubleClicked.connect(self._add_selected_to_cart)
        layout.addWidget(self.product_table)

        # Controles de cantidad + botón agregar
        add_row = QHBoxLayout()

        lbl_qty = QLabel("Cantidad:")
        lbl_qty.setStyleSheet("font-size: 13px;")

        self.qty_spin = QSpinBox()
        self.qty_spin.setMinimum(1)
        self.qty_spin.setMaximum(9999)
        self.qty_spin.setValue(1)
        self.qty_spin.setFixedHeight(34)
        self.qty_spin.setFixedWidth(80)
        self.qty_spin.setStyleSheet("font-size: 13px; padding: 2px 6px;")

        btn_add = QPushButton("➕  Agregar al carrito")
        btn_add.setStyleSheet(BTN_PRIMARY)
        btn_add.clicked.connect(self._add_selected_to_cart)

        add_row.addWidget(lbl_qty)
        add_row.addWidget(self.qty_spin)
        add_row.addStretch()
        add_row.addWidget(btn_add)
        layout.addLayout(add_row)

        return layout

    def _build_right_panel(self):
        """Panel derecho: carrito + total + botón confirmar."""
        layout = QVBoxLayout()
        layout.setSpacing(8)

        lbl = QLabel("Carrito de venta")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1F3864;")
        layout.addWidget(lbl)

        # Tabla del carrito
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(
            ["Producto", "Cant.", "Precio unit.", "Subtotal", ""]
        )
        self.cart_table.setStyleSheet(TBL_STYLE)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cart_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cart_table.setColumnWidth(1, 55)
        self.cart_table.setColumnWidth(2, 95)
        self.cart_table.setColumnWidth(3, 90)
        self.cart_table.setColumnWidth(4, 36)
        layout.addWidget(self.cart_table)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #D5D8DC;")
        layout.addWidget(sep)

        # Total
        total_row = QHBoxLayout()
        lbl_total = QLabel("TOTAL:")
        lbl_total.setStyleSheet("font-size: 15px; font-weight: bold;")
        self.lbl_total_value = QLabel("$ 0.00")
        self.lbl_total_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_total_value.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #1E8449;"
        )
        total_row.addWidget(lbl_total)
        total_row.addStretch()
        total_row.addWidget(self.lbl_total_value)
        layout.addLayout(total_row)

        # Botones
        btn_row = QHBoxLayout()

        self.btn_clear = QPushButton("🗑  Vaciar")
        self.btn_clear.setStyleSheet(BTN_DANGER)
        self.btn_clear.clicked.connect(self._clear_cart)

        self.btn_confirm = QPushButton("✅  Confirmar venta")
        self.btn_confirm.setStyleSheet(BTN_SUCCESS)
        self.btn_confirm.clicked.connect(self._confirm_sale)
        self.btn_confirm.setEnabled(False)

        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_confirm)
        layout.addLayout(btn_row)

        return layout

    # ── Lógica de productos ──────────────────────────────────────────────────

    def _load_products(self):
        """Carga todos los productos desde la BD."""
        result = self._inv.get_all()
        if result["success"]:
            self._all_products = result["data"]
            self._render_product_table(self._all_products)
        else:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los productos:\n{result['error']}")

    def _render_product_table(self, products: list[dict]):
        self.product_table.setRowCount(0)
        for p in products:
            row = self.product_table.rowCount()
            self.product_table.insertRow(row)

            self.product_table.setItem(row, 0, self._cell(str(p["id"]), Qt.AlignCenter))
            self.product_table.setItem(row, 1, self._cell(p["nombre"]))
            self.product_table.setItem(row, 2, self._cell(p["categoria"] or "—"))
            self.product_table.setItem(row, 3, self._cell(f"$ {p['precio']:,.0f}", Qt.AlignRight))
            stock_item = self._cell(str(p["cantidad"]), Qt.AlignCenter)
            if p["cantidad"] == 0:
                stock_item.setForeground(QColor("#C0392B"))
            layout: QHBoxLayout
            self.product_table.setItem(row, 4, stock_item)

    def _filter_products(self, text: str):
        text = text.lower().strip()
        if not text:
            self._render_product_table(self._all_products)
            return
        filtered = [
            p for p in self._all_products
            if text in p["nombre"].lower()
            or text in (p["categoria"] or "").lower()
        ]
        self._render_product_table(filtered)

    # ── Lógica del carrito ───────────────────────────────────────────────────

    def _add_selected_to_cart(self):
        row = self.product_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Seleccionar producto",
                                    "Selecciona un producto de la tabla primero.")
            return

        producto_id = int(self.product_table.item(row, 0).text())
        nombre      = self.product_table.item(row, 1).text()
        precio_text = self.product_table.item(row, 3).text().replace("$", "").replace(",", "").strip()
        precio_unit = float(precio_text)
        stock       = int(self.product_table.item(row, 4).text())
        cantidad    = self.qty_spin.value()

        if stock == 0:
            QMessageBox.warning(self, "Sin stock",
                                f"'{nombre}' no tiene stock disponible.")
            return

        if cantidad > stock:
            QMessageBox.warning(self, "Stock insuficiente",
                                f"Solo hay {stock} unidades disponibles de '{nombre}'.")
            return

        # Si el producto ya está en el carrito, actualizar cantidad
        for item in self._cart:
            if item["producto_id"] == producto_id:
                nueva_cant = item["cantidad"] + cantidad
                if nueva_cant > stock:
                    QMessageBox.warning(
                        self, "Stock insuficiente",
                        f"No puedes exceder {stock} unidades de '{nombre}'.\n"
                        f"Ya tienes {item['cantidad']} en el carrito."
                    )
                    return
                item["cantidad"] = nueva_cant
                self._refresh_cart()
                return

        self._cart.append({
            "producto_id": producto_id,
            "nombre":      nombre,
            "precio_unit": precio_unit,
            "cantidad":    cantidad,
            "stock":       stock,
        })
        self.qty_spin.setValue(1)
        self._refresh_cart()

    def _refresh_cart(self):
        """Re-dibuja la tabla del carrito y actualiza el total."""
        self.cart_table.setRowCount(0)
        total = 0.0

        for idx, item in enumerate(self._cart):
            subtotal = item["cantidad"] * item["precio_unit"]
            total += subtotal

            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            self.cart_table.setItem(row, 0, self._cell(item["nombre"]))
            self.cart_table.setItem(row, 1, self._cell(str(item["cantidad"]), Qt.AlignCenter))
            self.cart_table.setItem(row, 2, self._cell(f"$ {item['precio_unit']:,.0f}", Qt.AlignRight))
            self.cart_table.setItem(row, 3, self._cell(f"$ {subtotal:,.0f}", Qt.AlignRight))

            btn_del = QPushButton("✕")
            btn_del.setStyleSheet(BTN_DANGER)
            btn_del.clicked.connect(lambda _, i=idx: self._remove_from_cart(i))
            self.cart_table.setCellWidget(row, 4, btn_del)

        self.lbl_total_value.setText(f"$ {total:,.0f}")
        self.btn_confirm.setEnabled(len(self._cart) > 0)

    def _remove_from_cart(self, idx: int):
        self._cart.pop(idx)
        self._refresh_cart()

    def _clear_cart(self):
        if not self._cart:
            return
        resp = QMessageBox.question(self, "Vaciar carrito",
                                    "¿Deseas eliminar todos los productos del carrito?",
                                    QMessageBox.Yes | QMessageBox.No)
        if resp == QMessageBox.Yes:
            self._cart.clear()
            self._refresh_cart()

    # ── Confirmar venta ──────────────────────────────────────────────────────

    def _confirm_sale(self):
        if not self._cart:
            return

        vendedor_id = get_session()["id"]
        items = [
            {
                "producto_id": item["producto_id"],
                "cantidad":    item["cantidad"],
                "precio_unit": item["precio_unit"],
            }
            for item in self._cart
        ]

        result = self._sales.create_sale(vendedor_id, items)

        if result["success"]:
            venta_id = result["data"]
            self._show_summary(venta_id)
            self._cart.clear()
            self._refresh_cart()
            self._load_products()          # recargar stock actualizado
        else:
            QMessageBox.critical(self, "Error al registrar venta", result["error"])

    def _show_summary(self, venta_id: int):
        """Diálogo de resumen de venta."""
        dlg = QDialog(self)
        dlg.setWindowTitle("✅ Venta registrada")
        dlg.setFixedWidth(420)
        dlg.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(12)

        # Encabezado
        lbl_ok = QLabel("¡Venta registrada exitosamente!")
        lbl_ok.setAlignment(Qt.AlignCenter)
        lbl_ok.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E8449;")
        layout.addWidget(lbl_ok)

        lbl_id = QLabel(f"ID de venta: #{venta_id}")
        lbl_id.setAlignment(Qt.AlignCenter)
        lbl_id.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(lbl_id)

        lbl_vend = QLabel(f"Vendedor: {get_session()['nombre']}")
        lbl_vend.setAlignment(Qt.AlignCenter)
        lbl_vend.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(lbl_vend)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #D5D8DC;")
        layout.addWidget(sep)

        # Detalle de items
        total = 0.0
        for item in self._cart or []:
            subtotal = item["cantidad"] * item["precio_unit"]
            total += subtotal
            row_lbl = QLabel(
                f"  {item['nombre']}  ×{item['cantidad']}  →  $ {subtotal:,.0f}"
            )
            row_lbl.setStyleSheet("font-size: 13px;")
            layout.addWidget(row_lbl)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #D5D8DC;")
        layout.addWidget(sep2)

        # Re-calcular total desde los items (carrito ya vaciado al llamar _show_summary)
        total_lbl = QLabel(f"TOTAL: $ {float(self.lbl_total_value.text().replace('$','').replace(',','').strip()):,.0f}")
        total_lbl.setAlignment(Qt.AlignRight)
        total_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E8449;")
        layout.addWidget(total_lbl)

        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet(BTN_PRIMARY)
        btn_close.clicked.connect(dlg.accept)
        layout.addWidget(btn_close)

        dlg.exec()

    # ── Utilitarios ──────────────────────────────────────────────────────────

    @staticmethod
    def _cell(text: str, alignment=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        return item
