from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QMessageBox, QDialog, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from auth.session import get_session
from modules.inventory import InventoryManager
from modules.sales import SalesManager
from ui.receipt_preview import ReceiptPreviewDialog


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
    """Pagina principal del modulo de Ventas (HU-07)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._inv = InventoryManager()
        self._sales = SalesManager()
        self._cart: list[dict] = []
        self._all_products: list[dict] = []
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        title = QLabel("🛒  Registrar Venta")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F3864;")
        root.addWidget(title)

        body = QHBoxLayout()
        body.setSpacing(20)
        root.addLayout(body)

        body.addLayout(self._build_left_panel(), stretch=3)
        body.addLayout(self._build_right_panel(), stretch=2)

    def _build_left_panel(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        lbl = QLabel("Productos disponibles")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1F3864;")
        layout.addWidget(lbl)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Buscar por nombre o categoria...")
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

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Categoria", "Precio", "Stock"]
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
        layout = QVBoxLayout()
        layout.setSpacing(8)

        lbl = QLabel("Carrito de venta")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1F3864;")
        layout.addWidget(lbl)

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

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #D5D8DC;")
        layout.addWidget(sep)

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

    def _load_products(self):
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
            
            # Mostrar nombre con indicador de descuento si aplica
            nombre = p["nombre"]
            if p.get("descuento_activo") and p.get("descuento_pct", 0) > 0:
                nombre_item = self._cell(f"🎁 {nombre}")
                nombre_item.setForeground(QColor("#1E8449"))
                font = nombre_item.font()
                font.setBold(True)
                nombre_item.setFont(font)
                self.product_table.setItem(row, 1, nombre_item)
            else:
                self.product_table.setItem(row, 1, self._cell(nombre))
            
            self.product_table.setItem(row, 2, self._cell(p["categoria"] or "-"))
            
            # Mostrar precio con descuento tachado si aplica
            if p.get("descuento_activo") and p.get("descuento_pct", 0) > 0:
                desc_pct = p.get("descuento_pct", 0)
                precio_item = self._cell(f"$ {p['precio']:,.0f}", Qt.AlignRight)
                precio_item.setForeground(QColor("#A93226"))  # Rojo para destacar
                font = precio_item.font()
                font.setStrikeOut(True)
                precio_item.setFont(font)
                self.product_table.setItem(row, 3, precio_item)
            else:
                self.product_table.setItem(row, 3, self._cell(f"$ {p['precio']:,.0f}", Qt.AlignRight))
            
            stock_item = self._cell(str(p["cantidad"]), Qt.AlignCenter)
            if p["cantidad"] == 0:
                stock_item.setForeground(QColor("#C0392B"))
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

    def _add_selected_to_cart(self):
        row = self.product_table.currentRow()
        if row < 0:
            QMessageBox.information(
                self,
                "Seleccionar producto",
                "Selecciona un producto de la tabla primero."
            )
            return

        producto_id = int(self.product_table.item(row, 0).text())
        nombre = self.product_table.item(row, 1).text().replace("🎁 ", "")  # Remover el emoji de descuento si existe
        precio_text = self.product_table.item(row, 3).text().replace("$", "").replace(",", "").strip()
        precio_unit = float(precio_text)
        stock = int(self.product_table.item(row, 4).text())
        cantidad = self.qty_spin.value()

        # Obtener información del producto para descuentos
        producto_data = next((p for p in self._all_products if p["id"] == producto_id), None)
        if not producto_data:
            QMessageBox.warning(self, "Error", f"No se pudo encontrar la información del producto")
            return

        if stock == 0:
            QMessageBox.warning(self, "Sin stock", f"'{nombre}' no tiene stock disponible.")
            return

        if cantidad > stock:
            QMessageBox.warning(
                self,
                "Stock insuficiente",
                f"Solo hay {stock} unidades disponibles de '{nombre}'."
            )
            return

        for item in self._cart:
            if item["producto_id"] == producto_id:
                nueva_cant = item["cantidad"] + cantidad
                if nueva_cant > stock:
                    QMessageBox.warning(
                        self,
                        "Stock insuficiente",
                        f"No puedes exceder {stock} unidades de '{nombre}'.\nYa tienes {item['cantidad']} en el carrito."
                    )
                    return
                item["cantidad"] = nueva_cant
                self._refresh_cart()
                return

        self._cart.append({
            "producto_id": producto_id,
            "nombre": nombre,
            "precio_unit": precio_unit,
            "cantidad": cantidad,
            "stock": stock,
            "descuento_pct": producto_data.get("descuento_pct", 0),
            "descuento_activo": producto_data.get("descuento_activo", 0),
        })
        self.qty_spin.setValue(1)
        self._refresh_cart()

    def _refresh_cart(self):
        self.cart_table.setRowCount(0)
        total_bruto = 0.0
        total_descuentos = 0.0

        for idx, item in enumerate(self._cart):
            subtotal_bruto = item["cantidad"] * item["precio_unit"]
            descuento = 0.0
            
            # Calcular descuento si está activo
            if item.get("descuento_activo") and item.get("descuento_pct", 0) > 0:
                descuento = subtotal_bruto * (item.get("descuento_pct", 0) / 100.0)
            
            subtotal_neto = subtotal_bruto - descuento
            total_bruto += subtotal_bruto
            total_descuentos += descuento

            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            
            # Nombre con descuento si aplica
            nombre_display = item["nombre"]
            if descuento > 0:
                nombre_display = f"🎁 {item['nombre']} ({item.get('descuento_pct', 0):.0f}% OFF)"
            nombre_item = self._cell(nombre_display)
            if descuento > 0:
                nombre_item.setForeground(QColor("#1E8449"))
                font = nombre_item.font()
                font.setBold(True)
                nombre_item.setFont(font)
            self.cart_table.setItem(row, 0, nombre_item)
            
            self.cart_table.setItem(row, 1, self._cell(str(item["cantidad"]), Qt.AlignCenter))
            self.cart_table.setItem(row, 2, self._cell(f"$ {item['precio_unit']:,.0f}", Qt.AlignRight))
            
            # Mostrar subtotal neto (después del descuento)
            self.cart_table.setItem(row, 3, self._cell(f"$ {subtotal_neto:,.0f}", Qt.AlignRight))

            btn_del = QPushButton("✕")
            btn_del.setStyleSheet(BTN_DANGER)
            btn_del.clicked.connect(lambda _, i=idx: self._remove_from_cart(i))
            self.cart_table.setCellWidget(row, 4, btn_del)

        # Calcular total final
        total_final = total_bruto - total_descuentos
        
        # Mostrar total con detalles de descuentos
        if total_descuentos > 0:
            self.lbl_total_value.setText(f"$ {total_final:,.0f}")
            self.lbl_total_value.setToolTip(f"Subtotal: ${total_bruto:,.0f} - Descuentos: ${total_descuentos:,.0f}")
        else:
            self.lbl_total_value.setText(f"$ {total_final:,.0f}")
            self.lbl_total_value.setToolTip("")
        
        self.btn_confirm.setEnabled(len(self._cart) > 0)

    def _remove_from_cart(self, idx: int):
        self._cart.pop(idx)
        self._refresh_cart()

    def _clear_cart(self):
        if not self._cart:
            return
        resp = QMessageBox.question(
            self,
            "Vaciar carrito",
            "¿Deseas eliminar todos los productos del carrito?",
            QMessageBox.Yes | QMessageBox.No
        )
        if resp == QMessageBox.Yes:
            self._cart.clear()
            self._refresh_cart()

    def _confirm_sale(self):
        if not self._cart:
            return

        vendedor_id = get_session()["id"]
        items = [
            {
                "producto_id": item["producto_id"],
                "cantidad": item["cantidad"],
                "precio_unit": item["precio_unit"],
            }
            for item in self._cart
        ]

        result = self._sales.create_sale(vendedor_id, items)

        if not result["success"]:
            QMessageBox.critical(self, "Error al registrar venta", result["error"])
            return

        venta_id = result["data"]
        sale_result = self._sales.get_sale(venta_id)

        self._cart.clear()
        self._refresh_cart()
        self._load_products()

        if not sale_result["success"]:
            QMessageBox.critical(
                self,
                "Error",
                f"La venta #{venta_id} se registro, pero no se pudo cargar el recibo:\n{sale_result['error']}"
            )
            return

        # Abrir automáticamente el preview del recibo después de confirmar la venta
        dlg = ReceiptPreviewDialog(sale_result["data"], parent=self)
        dlg.exec()


    @staticmethod
    def _cell(text: str, alignment=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        return item
