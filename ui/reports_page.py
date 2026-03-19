from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QDateEdit, QMessageBox
)

from modules.reports import ReportManager
from modules.sales import SalesManager
from ui.receipt_preview import ReceiptPreviewDialog
from ui.report_preview import ReportPreviewDialog


BTN_PRIMARY = """
    QPushButton {
        background-color: #2E86C1; color: white;
        border: none; border-radius: 6px;
        font-size: 13px; font-weight: bold; padding: 8px 18px;
    }
    QPushButton:hover   { background-color: #1A6FA3; }
    QPushButton:pressed { background-color: #145A87; }
"""
BTN_REPORT = """
    QPushButton {
        background-color: #6C3483; color: white;
        border: none; border-radius: 6px;
        font-size: 13px; font-weight: bold; padding: 8px 18px;
    }
    QPushButton:hover   { background-color: #5B2C6F; }
    QPushButton:pressed { background-color: #4A235A; }
"""
BTN_RECEIPT = """
    QPushButton {
        background-color: #1E8449; color: white;
        border: none; border-radius: 6px;
        font-size: 12px; font-weight: bold; padding: 7px 16px;
    }
    QPushButton:hover   { background-color: #196F3D; }
    QPushButton:pressed { background-color: #145A32; }
    QPushButton:disabled { background-color: #AAB7B8; }
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
TBL_DETAIL_STYLE = """
    QTableWidget {
        border: 1px solid #D5D8DC;
        border-radius: 4px;
        gridline-color: #EBF0F0;
        font-size: 12px;
        background-color: #FDFEFE;
    }
    QHeaderView::section {
        background-color: #2E5FA3;
        color: white;
        padding: 4px;
        border: none;
        font-size: 12px;
    }
"""


class ReportsPage(QWidget):
    """Pagina de reporte diario e historial inmediato de ventas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = ReportManager()
        self._sales = SalesManager()
        self._ventas: list[dict] = []
        self._selected_sale_id = None
        self._build_ui()
        self._load_report()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        header_row = QHBoxLayout()

        title = QLabel("📊  Reporte de Ventas del Dia")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F3864;")
        header_row.addWidget(title)

        header_row.addStretch()

        lbl_fecha_txt = QLabel("Fecha:")
        lbl_fecha_txt.setStyleSheet("font-size: 13px; color: #555;")
        header_row.addWidget(lbl_fecha_txt)

        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setMaximumDate(QDate.currentDate())
        self.date_picker.setFixedHeight(34)
        self.date_picker.setStyleSheet("""
            QDateEdit {
                border: 1px solid #AEB6BF;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 13px;
            }
            QDateEdit:focus { border-color: #2E86C1; }
        """)
        self.date_picker.dateChanged.connect(self._load_report)
        header_row.addWidget(self.date_picker)

        btn_refresh = QPushButton("🔄  Actualizar")
        btn_refresh.setStyleSheet(BTN_PRIMARY)
        btn_refresh.clicked.connect(self._load_report)
        header_row.addWidget(btn_refresh)

        sep_v = QFrame()
        sep_v.setFrameShape(QFrame.VLine)
        sep_v.setStyleSheet("color: #A8C4E8;")
        sep_v.setFixedWidth(1)
        header_row.addWidget(sep_v)

        self.btn_reporte_dia = QPushButton("📄  Reporte del Dia")
        self.btn_reporte_dia.setStyleSheet(BTN_REPORT)
        self.btn_reporte_dia.setToolTip(
            "Genera un reporte completo del dia seleccionado\ncon previsualizacion, impresion y exportacion a PDF."
        )
        self.btn_reporte_dia.clicked.connect(self._open_report_preview)
        header_row.addWidget(self.btn_reporte_dia)

        root.addLayout(header_row)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self.card_ventas = self._make_card("Total de ventas", "0", "#1F3864")
        self.card_ingresos = self._make_card("Ingresos del dia", "$ 0", "#1E8449")

        cards_row.addWidget(self.card_ventas)
        cards_row.addWidget(self.card_ingresos)
        cards_row.addStretch()
        root.addLayout(cards_row)

        lbl_tabla = QLabel("Transacciones")
        lbl_tabla.setStyleSheet("font-size: 14px; font-weight: bold; color: #1F3864;")
        root.addWidget(lbl_tabla)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["# Venta", "Hora", "Vendedor", "Monto"])
        self.table.setStyleSheet(TBL_STYLE)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 100)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(3, 130)
        self.table.clicked.connect(self._on_row_selected)
        root.addWidget(self.table, stretch=2)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #D5D8DC;")
        root.addWidget(sep)

        detail_header = QHBoxLayout()

        self.lbl_detalle_titulo = QLabel("Selecciona una venta para ver el detalle de productos")
        self.lbl_detalle_titulo.setStyleSheet("font-size: 13px; font-weight: bold; color: #1F3864;")
        detail_header.addWidget(self.lbl_detalle_titulo)
        detail_header.addStretch()

        self.btn_receipt = QPushButton("Recibo imprimible")
        self.btn_receipt.setStyleSheet(BTN_RECEIPT)
        self.btn_receipt.setEnabled(False)
        self.btn_receipt.clicked.connect(self._open_sale_receipt)
        detail_header.addWidget(self.btn_receipt)

        root.addLayout(detail_header)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(4)
        self.detail_table.setHorizontalHeaderLabels(["Producto", "Cantidad", "Precio unit.", "Subtotal"])
        self.detail_table.setStyleSheet(TBL_DETAIL_STYLE)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.detail_table.setColumnWidth(1, 80)
        self.detail_table.setColumnWidth(2, 110)
        self.detail_table.setColumnWidth(3, 110)
        self.detail_table.setFixedHeight(160)
        root.addWidget(self.detail_table)

        self.lbl_empty = QLabel("📭  No hay ventas registradas para el dia de hoy.")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.lbl_empty.setStyleSheet("font-size: 15px; color: #888; padding: 20px;")
        self.lbl_empty.hide()
        root.addWidget(self.lbl_empty)

    def _load_report(self):
        qdate = self.date_picker.date()
        fecha = qdate.toString("yyyy-MM-dd")

        result = self._manager.get_daily_report(fecha)

        if not result["success"]:
            self.lbl_detalle_titulo.setText(f"Error al cargar el reporte: {result['error']}")
            self.btn_receipt.setEnabled(False)
            return

        data = result["data"]
        self._ventas = data["ventas"]
        self._selected_sale_id = None
        self.btn_receipt.setEnabled(False)

        self._update_card(self.card_ventas, "Total de ventas", str(data["num_ventas"]))
        self._update_card(self.card_ingresos, "Ingresos del dia", f"$ {data['total_dia']:,.0f}")

        if not self._ventas:
            self.table.setRowCount(0)
            self.detail_table.setRowCount(0)
            self.lbl_empty.show()
            self.table.hide()
            self.lbl_detalle_titulo.setText("No hay ventas para mostrar.")
        else:
            self.lbl_empty.hide()
            self.table.show()
            self._render_table()
            self.lbl_detalle_titulo.setText("Selecciona una venta para ver el detalle de productos")
            self.detail_table.setRowCount(0)

    def _render_table(self):
        self.table.setRowCount(0)
        for v in self._ventas:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, self._cell(f"#{v['venta_id']}", Qt.AlignCenter))
            self.table.setItem(row, 1, self._cell(v["hora"], Qt.AlignCenter))
            self.table.setItem(row, 2, self._cell(v["vendedor"]))
            monto = self._cell(f"$ {v['total']:,.0f}", Qt.AlignRight | Qt.AlignVCenter)
            monto.setForeground(QColor("#1E8449"))
            font = QFont()
            font.setBold(True)
            monto.setFont(font)
            self.table.setItem(row, 3, monto)

    def _on_row_selected(self, index):
        row = index.row()
        if row < 0 or row >= len(self._ventas):
            return

        venta = self._ventas[row]
        self._selected_sale_id = venta["venta_id"]
        self.btn_receipt.setEnabled(True)
        self.lbl_detalle_titulo.setText(
            f"Detalle venta #{venta['venta_id']}  -  {venta['vendedor']}  -  {venta['hora']}"
        )

        self.detail_table.setRowCount(0)
        for p in venta["productos"]:
            r = self.detail_table.rowCount()
            self.detail_table.insertRow(r)
            self.detail_table.setItem(r, 0, self._cell(p["nombre"]))
            self.detail_table.setItem(r, 1, self._cell(str(p["cantidad"]), Qt.AlignCenter))
            self.detail_table.setItem(r, 2, self._cell(f"$ {p['precio_unit']:,.0f}", Qt.AlignRight))
            self.detail_table.setItem(r, 3, self._cell(f"$ {p['subtotal']:,.0f}", Qt.AlignRight))

    def _open_sale_receipt(self):
        if not self._selected_sale_id:
            return

        result = self._sales.get_sale(self._selected_sale_id)
        if not result["success"]:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el recibo:\n{result['error']}")
            return

        dlg = ReceiptPreviewDialog(result["data"], parent=self)
        dlg.exec()

    def _make_card(self, titulo: str, valor: str, color: str) -> QWidget:
        card = QWidget()
        card.setFixedSize(220, 80)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 10px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(2)

        lbl_title = QLabel(titulo)
        lbl_title.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")
        lbl_title.setObjectName("card_title")

        lbl_value = QLabel(valor)
        lbl_value.setStyleSheet("color: white; font-size: 22px; font-weight: bold;")
        lbl_value.setObjectName("card_value")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        return card

    def _update_card(self, card: QWidget, titulo: str, valor: str):
        card.findChild(QLabel, "card_title").setText(titulo)
        card.findChild(QLabel, "card_value").setText(valor)

    @staticmethod
    def _cell(text: str, alignment=Qt.AlignLeft | Qt.AlignVCenter) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(alignment)
        return item

    def _open_report_preview(self):
        qdate = self.date_picker.date()
        fecha = qdate.toString("yyyy-MM-dd")

        result = self._manager.get_daily_report(fecha)

        if not result["success"]:
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte:\n{result['error']}")
            return

        dlg = ReportPreviewDialog(result["data"], parent=self)
        dlg.exec()
