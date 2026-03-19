from datetime import datetime
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QPageSize, QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


BTN_PRIMARY = """
    QPushButton {
        background-color: #2E86C1; color: white;
        border: none; border-radius: 6px;
        font-size: 13px; font-weight: bold; padding: 9px 20px;
    }
    QPushButton:hover   { background-color: #1A6FA3; }
    QPushButton:pressed { background-color: #145A87; }
"""
BTN_SUCCESS = """
    QPushButton {
        background-color: #1E8449; color: white;
        border: none; border-radius: 6px;
        font-size: 13px; font-weight: bold; padding: 9px 20px;
    }
    QPushButton:hover   { background-color: #196F3D; }
    QPushButton:pressed { background-color: #145A32; }
"""
BTN_SECONDARY = """
    QPushButton {
        background-color: #F0F0F0; color: #333;
        border: 1px solid #CCC; border-radius: 6px;
        font-size: 13px; padding: 9px 20px;
    }
    QPushButton:hover   { background-color: #E0E0E0; }
    QPushButton:pressed { background-color: #D0D0D0; }
"""


class ReceiptPreviewDialog(QDialog):
    """Previsualización, impresión y exportación del recibo de una venta."""

    def __init__(self, sale_data: dict, parent=None):
        super().__init__(parent)
        self._sale_data = sale_data
        self._html = self._build_html()

        self.setWindowTitle("Previsualización - Recibo de venta")
        self.setMinimumSize(860, 720)
        self.resize(900, 760)
        self.setStyleSheet("background-color: #F4F6F7;")

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background-color: #1F3864;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("Recibo / Factura de venta")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch()

        txn = self._sale_data.get("numero_transaccion", f"#{self._sale_data.get('venta_id', '')}")
        meta = QLabel(f"Transaccion {txn}")
        meta.setStyleSheet("color: #A8C4E8; font-size: 12px;")
        toolbar_layout.addWidget(meta)

        root.addWidget(toolbar)

        self.browser = QTextBrowser()
        self.browser.setReadOnly(True)
        self.browser.setOpenExternalLinks(False)
        self.browser.setStyleSheet("border: none; background-color: #E8ECF0; padding: 24px;")
        self.browser.setHtml(self._html)
        root.addWidget(self.browser, stretch=1)

        actions = QWidget()
        actions.setFixedHeight(68)
        actions.setStyleSheet("background-color: white; border-top: 1px solid #D5D8DC;")
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(24, 0, 24, 0)
        actions_layout.setSpacing(12)

        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet(BTN_SECONDARY)
        btn_close.clicked.connect(self.reject)

        btn_print = QPushButton("Imprimir")
        btn_print.setStyleSheet(BTN_PRIMARY)
        btn_print.clicked.connect(self._print_receipt)

        btn_export = QPushButton("Exportar PDF")
        btn_export.setStyleSheet(BTN_SUCCESS)
        btn_export.clicked.connect(self._export_pdf)

        actions_layout.addWidget(btn_close)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_print)
        actions_layout.addWidget(btn_export)
        root.addWidget(actions)

    def _build_document(self):
        document = QTextDocument(self)
        document.setDocumentMargin(24)
        document.setHtml(self._html)
        return document

    def _send_to_printer(self, printer):
        document = self._build_document()
        # Evita que Qt escale todo el documento para "hacerlo caber", lo que
        # termina dejando el texto demasiado pequeno en el PDF.
        document.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
        # PySide6 expone print_ por colision con la palabra reservada print.
        print_fn = getattr(document, "print_", None) or getattr(document, "print", None)
        if not print_fn:
            raise AttributeError("QTextDocument no tiene metodo de impresion disponible.")
        print_fn(printer)

    def _build_html(self) -> str:
        sale = self._sale_data
        items = sale.get("items", [])
        txn = escape(sale.get("numero_transaccion", f"#{sale.get('venta_id', '')}"))
        negocio = escape(sale.get("negocio", "Negocio"))
        vendedor = escape(sale.get("vendedor", "Sin vendedor"))
        fecha_hora = escape(self._fmt_datetime(sale.get("fecha_hora")))
        subtotal = sale.get("subtotal", sale.get("total", 0.0))
        descuentos = sale.get("total_descuentos", 0.0)
        total = sale.get("total", 0.0)

        rows = []
        for item in items:
            descuento = item.get("descuento_monto", 0.0)
            if descuento:
                descuento_text = f"-{self._money(descuento)}"
            else:
                descuento_text = "No aplica"

            rows.append(f"""
                <tr>
                    <td>{escape(item.get('nombre', ''))}</td>
                    <td class="center">{item.get('cantidad', 0)}</td>
                    <td class="right">{self._money(item.get('precio_unit', 0.0))}</td>
                    <td class="right">{descuento_text}</td>
                    <td class="right">{self._money(item.get('subtotal', 0.0))}</td>
                </tr>
            """)

        detail_rows = "".join(rows) or (
            '<tr><td colspan="5" class="empty">No hay productos en esta venta.</td></tr>'
        )

        resumen_descuento = (
            f'<div class="summary-row"><span>Descuentos aplicados</span><strong>-{self._money(descuentos)}</strong></div>'
            if descuentos else
            '<div class="summary-row muted"><span>Descuentos aplicados</span><strong>No aplica</strong></div>'
        )

        return f"""
        <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{
                        background: #E8ECF0;
                        font-family: 'DejaVu Sans', Arial, sans-serif;
                        color: #1C2833;
                        margin: 0;
                        padding: 18px;
                    }}
                    .page {{
                        max-width: 760px;
                        margin: 0 auto;
                        background: white;
                        border: 1px solid #D5D8DC;
                        border-radius: 8px;
                        padding: 34px 38px;
                    }}
                    .brand {{
                        text-align: center;
                        margin-bottom: 18px;
                    }}
                    .brand h1 {{
                        font-size: 26px;
                        margin: 0;
                        color: #1F3864;
                    }}
                    .brand p {{
                        margin: 6px 0 0;
                        color: #55708F;
                        font-size: 12px;
                    }}
                    .title {{
                        text-align: center;
                        font-size: 18px;
                        font-weight: bold;
                        color: #1F3864;
                        margin-bottom: 22px;
                        padding-bottom: 12px;
                        border-bottom: 2px solid #1F3864;
                    }}
                    .meta {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 22px;
                    }}
                    .meta td {{
                        padding: 6px 0;
                        font-size: 12px;
                    }}
                    .meta .label {{
                        color: #5D6D7E;
                        width: 32%;
                    }}
                    table.detail {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 8px;
                    }}
                    table.detail th {{
                        background: #1F3864;
                        color: white;
                        font-size: 11px;
                        font-weight: bold;
                        padding: 10px 8px;
                        text-align: left;
                    }}
                    table.detail td {{
                        border-bottom: 1px solid #E5E8E8;
                        padding: 10px 8px;
                        font-size: 12px;
                    }}
                    table.detail tr:nth-child(even) td {{
                        background: #F8FAFB;
                    }}
                    .right {{ text-align: right; }}
                    .center {{ text-align: center; }}
                    .empty {{
                        text-align: center;
                        color: #7B8794;
                        padding: 18px;
                    }}
                    .summary {{
                        margin-top: 22px;
                        margin-left: auto;
                        width: 280px;
                    }}
                    .summary-row {{
                        display: flex;
                        justify-content: space-between;
                        padding: 6px 0;
                        font-size: 13px;
                    }}
                    .summary-row.total {{
                        border-top: 2px solid #1F3864;
                        margin-top: 8px;
                        padding-top: 10px;
                        font-size: 16px;
                        color: #1E8449;
                    }}
                    .summary-row.muted {{
                        color: #6C7A89;
                    }}
                    .footer {{
                        margin-top: 34px;
                        padding-top: 14px;
                        border-top: 1px solid #D5D8DC;
                        text-align: center;
                        color: #7B8794;
                        font-size: 11px;
                    }}
                </style>
            </head>
            <body>
                <div class="page">
                    <div class="brand">
                        <h1>{negocio}</h1>
                        <p>Comprobante formal de venta</p>
                    </div>
                    <div class="title">RECIBO / FACTURA DE VENTA</div>

                    <table class="meta">
                        <tr>
                            <td class="label">Fecha y hora</td>
                            <td>{fecha_hora}</td>
                        </tr>
                        <tr>
                            <td class="label">Numero de transaccion</td>
                            <td>{txn}</td>
                        </tr>
                        <tr>
                            <td class="label">Vendedor</td>
                            <td>{vendedor}</td>
                        </tr>
                    </table>

                    <table class="detail">
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th class="center">Cant.</th>
                                <th class="right">Precio unit.</th>
                                <th class="right">Descuento</th>
                                <th class="right">Subtotal</th>
                            </tr>
                        </thead>
                        <tbody>
                            {detail_rows}
                        </tbody>
                    </table>

                    <div class="summary">
                        <div class="summary-row"><span>Subtotal</span><strong>{self._money(subtotal)}</strong></div>
                        {resumen_descuento}
                        <div class="summary-row total"><span>Total final</span><strong>{self._money(total)}</strong></div>
                    </div>

                    <div class="footer">
                        Documento generado desde Mini-Sistema POS para impresion o exportacion PDF.
                    </div>
                </div>
            </body>
        </html>
        """

    def _print_receipt(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.Letter))

        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Imprimir recibo")

        if dialog.exec() != QPrintDialog.Accepted:
            return

        try:
            self._send_to_printer(printer)
        except Exception as e:
            QMessageBox.critical(self, "Error al imprimir", str(e))

    def _export_pdf(self):
        venta_id = self._sale_data.get("venta_id", "venta")
        default_name = f"recibo_venta_{venta_id}.pdf"

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar recibo como PDF",
            default_name,
            "Archivos PDF (*.pdf)"
        )

        if not dest:
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(dest)
        printer.setPageSize(QPageSize(QPageSize.Letter))

        try:
            self._send_to_printer(printer)
            QMessageBox.information(self, "PDF exportado", f"El recibo se guardo correctamente en:\n{dest}")
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))

    @staticmethod
    def _fmt_datetime(value: str) -> str:
        if not value:
            return "Sin fecha"

        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(value, fmt).strftime("%d/%m/%Y %H:%M")
            except ValueError:
                continue
        return value

    @staticmethod
    def _money(value: float) -> str:
        return f"$ {value:,.0f}"
