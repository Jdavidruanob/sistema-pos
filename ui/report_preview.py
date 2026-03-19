"""
report_preview.py
Ventana de previsualización del reporte diario de ventas.
Permite imprimir y exportar como PDF.
"""

import os
import shutil

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QMessageBox, QScrollArea,
    QWidget, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl, QThread, Signal
from PySide6.QtGui import QDesktopServices, QPixmap, QImage, QPageSize
from PySide6.QtPrintSupport import QPrinter, QPrintDialog

from ui.report_generator import ReportGenerator


# ── Estilos ───────────────────────────────────────────────────────────────────
BTN_PRIMARY = """
    QPushButton {
        background-color: #2E86C1; color: white;
        border: none; border-radius: 6px;
        font-size: 13px; font-weight: bold; padding: 9px 20px;
    }
    QPushButton:hover   { background-color: #1A6FA3; }
    QPushButton:pressed { background-color: #145A87; }
    QPushButton:disabled { background-color: #AAAAAA; }
"""
BTN_SUCCESS = """
    QPushButton {
        background-color: #1E8449; color: white;
        border: none; border-radius: 6px;
        font-size: 13px; font-weight: bold; padding: 9px 20px;
    }
    QPushButton:hover   { background-color: #196F3D; }
    QPushButton:pressed { background-color: #145A32; }
    QPushButton:disabled { background-color: #AAAAAA; }
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


class ReportPreviewDialog(QDialog):
    """
    Diálogo de previsualización del reporte diario.
    Muestra el HTML del reporte y permite imprimir o exportar a PDF.
    """

    def __init__(self, data: dict, parent=None):
        super().__init__(parent)
        self._data    = data
        self._pdf_path = None           # ruta del PDF temporal generado

        self.setWindowTitle("Previsualización — Reporte Diario de Ventas")
        self.setMinimumSize(820, 680)
        self.resize(860, 720)
        self.setStyleSheet("background-color: #F4F6F7;")

        self._build_ui()
        self._generate_pdf()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Barra superior ────────────────────────────────────────────────────
        toolbar = QWidget()
        toolbar.setFixedHeight(60)
        toolbar.setStyleSheet("background-color: #1F3864;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(20, 0, 20, 0)

        lbl_titulo = QLabel("📄  Reporte Diario de Ventas")
        lbl_titulo.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        tb_layout.addWidget(lbl_titulo)
        tb_layout.addStretch()

        self.lbl_estado = QLabel("Generando reporte...")
        self.lbl_estado.setStyleSheet("color: #A8C4E8; font-size: 12px;")
        tb_layout.addWidget(self.lbl_estado)

        root.addWidget(toolbar)

        # ── Área de previsualización (tabla HTML) ─────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: #E8ECF0;")

        preview_container = QWidget()
        preview_container.setStyleSheet("background-color: #E8ECF0;")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(30, 24, 30, 24)
        preview_layout.setSpacing(0)

        # Card que simula la hoja de papel
        self.paper = QWidget()
        self.paper.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 4px;
                border: 1px solid #D5D8DC;
            }
        """)
        self.paper.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.paper_layout = QVBoxLayout(self.paper)
        self.paper_layout.setContentsMargins(30, 30, 30, 30)
        self.paper_layout.setSpacing(6)

        # Contenido del reporte (se construye en _populate_preview)
        self.lbl_loading = QLabel("⏳  Generando vista previa...")
        self.lbl_loading.setAlignment(Qt.AlignCenter)
        self.lbl_loading.setStyleSheet("font-size: 14px; color: #888; padding: 40px;")
        self.paper_layout.addWidget(self.lbl_loading)

        preview_layout.addWidget(self.paper)
        scroll.setWidget(preview_container)
        root.addWidget(scroll, stretch=1)

        # ── Barra de acciones ─────────────────────────────────────────────────
        actions = QWidget()
        actions.setFixedHeight(64)
        actions.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #D5D8DC;
            }
        """)
        act_layout = QHBoxLayout(actions)
        act_layout.setContentsMargins(24, 0, 24, 0)
        act_layout.setSpacing(12)

        btn_close = QPushButton("Cerrar")
        btn_close.setStyleSheet(BTN_SECONDARY)
        btn_close.clicked.connect(self.reject)

        act_layout.addWidget(btn_close)
        act_layout.addStretch()

        self.btn_print = QPushButton("🖨️  Imprimir")
        self.btn_print.setStyleSheet(BTN_PRIMARY)
        self.btn_print.setEnabled(False)
        self.btn_print.clicked.connect(self._print_report)

        self.btn_export = QPushButton("📥  Exportar PDF")
        self.btn_export.setStyleSheet(BTN_SUCCESS)
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self._export_pdf)

        act_layout.addWidget(self.btn_print)
        act_layout.addWidget(self.btn_export)
        root.addWidget(actions)

    # ── Generación ────────────────────────────────────────────────────────────

    def _generate_pdf(self):
        """Genera el PDF temporal y actualiza la previsualización."""
        try:
            self._pdf_path = ReportGenerator.build(self._data)
            self._populate_preview()
            self.lbl_estado.setText("✅  Reporte listo")
            self.btn_print.setEnabled(True)
            self.btn_export.setEnabled(True)
        except Exception as e:
            self.lbl_estado.setText("❌  Error al generar")
            self.lbl_loading.setText(f"Error generando el reporte:\n{e}")

    def _populate_preview(self):
        """Construye la previsualización HTML del reporte dentro del 'papel'."""
        # Limpiar loading
        for i in reversed(range(self.paper_layout.count())):
            w = self.paper_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        data    = self._data
        ventas  = data["ventas"]
        fecha   = ReportGenerator._fmt_fecha(data["fecha"])

        def lbl(text, style=""):
            l = QLabel(text)
            l.setWordWrap(True)
            if style:
                l.setStyleSheet(style)
            return l

        def sep(height=1, color="#D5D8DC"):
            f = QFrame()
            f.setFrameShape(QFrame.HLine)
            f.setFixedHeight(height)
            f.setStyleSheet(f"background-color: {color}; border: none;")
            return f

        # Encabezado
        self.paper_layout.addWidget(lbl(
            "EMPRESA XYZ",
            "font-size: 20px; font-weight: bold; color: #1F3864; qproperty-alignment: AlignCenter;"
        ))
        self.paper_layout.addWidget(lbl(
            "Mini-Sistema POS",
            "font-size: 12px; color: #2E5FA3; qproperty-alignment: AlignCenter; margin-bottom: 4px;"
        ))
        self.paper_layout.addWidget(sep(2, "#1F3864"))
        self.paper_layout.addSpacing(8)
        self.paper_layout.addWidget(lbl(
            "REPORTE DIARIO DE VENTAS",
            "font-size: 14px; font-weight: bold; color: #1F3864; qproperty-alignment: AlignCenter;"
        ))
        self.paper_layout.addWidget(lbl(
            fecha,
            "font-size: 11px; color: #2E5FA3; qproperty-alignment: AlignCenter;"
        ))
        self.paper_layout.addSpacing(14)

        # Tarjetas de resumen
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        for titulo, valor, color in [
            ("Transacciones del día", str(data["num_ventas"]), "#1F3864"),
            ("Total de ingresos", f"$ {data['total_dia']:,.0f}", "#1E8449"),
        ]:
            card = QWidget()
            card.setStyleSheet(f"background-color: {color}; border-radius: 8px;")
            cl = QVBoxLayout(card)
            cl.setContentsMargins(16, 10, 16, 10)
            tl = QLabel(titulo)
            tl.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 10px; background: transparent;")
            vl = QLabel(valor)
            vl.setStyleSheet("color: white; font-size: 20px; font-weight: bold; background: transparent;")
            cl.addWidget(tl)
            cl.addWidget(vl)
            cards_row.addWidget(card)

        cards_widget = QWidget()
        cards_widget.setLayout(cards_row)
        self.paper_layout.addWidget(cards_widget)
        self.paper_layout.addSpacing(16)

        if not ventas:
            self.paper_layout.addWidget(sep())
            self.paper_layout.addSpacing(20)
            self.paper_layout.addWidget(lbl(
                "📭  No se registraron ventas durante este día.",
                "font-size: 14px; color: #888; qproperty-alignment: AlignCenter; padding: 20px;"
            ))
            self.paper_layout.addWidget(lbl(
                "El cierre de caja no presenta movimientos.",
                "font-size: 11px; color: #AAA; qproperty-alignment: AlignCenter;"
            ))
            self.paper_layout.addStretch()
            return

        # Tabla de ventas
        self.paper_layout.addWidget(lbl(
            "Detalle de transacciones",
            "font-size: 12px; font-weight: bold; color: #1F3864;"
        ))
        self.paper_layout.addSpacing(4)

        from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        from PySide6.QtGui import QColor, QFont

        tbl = QTableWidget()
        tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels(["#", "Hora", "Vendedor", "Productos", "Monto"])
        tbl.setEditTriggers(QTableWidget.NoEditTriggers)
        tbl.verticalHeader().setVisible(False)
        tbl.setAlternatingRowColors(True)
        tbl.setSelectionMode(QTableWidget.NoSelection)
        tbl.setFocusPolicy(Qt.NoFocus)
        tbl.setStyleSheet("""
            QTableWidget {
                border: 1px solid #D5D8DC;
                gridline-color: #EBF0F0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #1F3864; color: white;
                padding: 5px; border: none; font-weight: bold; font-size: 11px;
            }
            QTableWidget::item { padding: 4px; }
        """)

        hdr = tbl.horizontalHeader()
        tbl.setColumnWidth(0, 55)
        tbl.setColumnWidth(1, 75)
        tbl.setColumnWidth(2, 120)
        hdr.setSectionResizeMode(3, QHeaderView.Stretch)
        tbl.setColumnWidth(4, 100)

        for v in ventas:
            r = tbl.rowCount()
            tbl.insertRow(r)

            productos_str = ReportGenerator._resumir_productos(v["productos"])

            def cell(txt, align=Qt.AlignLeft | Qt.AlignVCenter):
                it = QTableWidgetItem(txt)
                it.setTextAlignment(align)
                return it

            tbl.setItem(r, 0, cell(f"#{v['venta_id']}", Qt.AlignCenter))
            tbl.setItem(r, 1, cell(v["hora"], Qt.AlignCenter))
            tbl.setItem(r, 2, cell(v["vendedor"]))
            tbl.setItem(r, 3, cell(productos_str))

            monto_item = cell(f"$ {v['total']:,.0f}", Qt.AlignRight | Qt.AlignVCenter)
            monto_item.setForeground(QColor("#1E8449"))
            f = QFont()
            f.setBold(True)
            monto_item.setFont(f)
            tbl.setItem(r, 4, monto_item)

        row_h = 28
        tbl.setFixedHeight(min(len(ventas) * row_h + 38, 320))
        self.paper_layout.addWidget(tbl)

        # Total
        self.paper_layout.addSpacing(4)
        total_lbl = QLabel(f"TOTAL DEL DÍA:  $ {data['total_dia']:,.0f}")
        total_lbl.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #1E8449;
            qproperty-alignment: AlignRight;
            border-top: 2px solid #1F3864;
            padding-top: 6px;
        """)
        self.paper_layout.addWidget(total_lbl)
        self.paper_layout.addSpacing(16)

        # Desglose por vendedor
        from collections import defaultdict
        vendedores = defaultdict(lambda: {"total": 0.0, "num": 0})
        for v in ventas:
            vendedores[v["vendedor"]]["total"] += v["total"]
            vendedores[v["vendedor"]]["num"]   += 1

        if len(vendedores) > 1:
            self.paper_layout.addWidget(sep())
            self.paper_layout.addSpacing(10)
            self.paper_layout.addWidget(lbl(
                "Desglose por vendedor",
                "font-size: 12px; font-weight: bold; color: #1F3864;"
            ))
            self.paper_layout.addSpacing(4)

            dv_tbl = QTableWidget()
            dv_tbl.setColumnCount(3)
            dv_tbl.setHorizontalHeaderLabels(["Vendedor", "Transacciones", "Total vendido"])
            dv_tbl.setEditTriggers(QTableWidget.NoEditTriggers)
            dv_tbl.verticalHeader().setVisible(False)
            dv_tbl.setSelectionMode(QTableWidget.NoSelection)
            dv_tbl.setFocusPolicy(Qt.NoFocus)
            dv_tbl.setAlternatingRowColors(True)
            dv_tbl.setStyleSheet(tbl.styleSheet())
            dv_tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            dv_tbl.setColumnWidth(1, 120)
            dv_tbl.setColumnWidth(2, 130)

            for nombre, stats in sorted(vendedores.items()):
                r = dv_tbl.rowCount()
                dv_tbl.insertRow(r)
                dv_tbl.setItem(r, 0, QTableWidgetItem(nombre))
                it_n = QTableWidgetItem(str(stats["num"]))
                it_n.setTextAlignment(Qt.AlignCenter)
                dv_tbl.setItem(r, 1, it_n)
                it_t = QTableWidgetItem(f"$ {stats['total']:,.0f}")
                it_t.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                it_t.setForeground(QColor("#1E8449"))
                dv_tbl.setItem(r, 2, it_t)

            dv_tbl.setFixedHeight(len(vendedores) * row_h + 38)
            self.paper_layout.addWidget(dv_tbl)
            self.paper_layout.addSpacing(12)

        # Pie
        self.paper_layout.addStretch()
        self.paper_layout.addWidget(sep())
        self.paper_layout.addSpacing(6)
        self.paper_layout.addWidget(lbl(
            f"Documento generado automáticamente — Mini-Sistema POS  ·  Cierre de caja {fecha}",
            "font-size: 9px; color: #AAA; qproperty-alignment: AlignCenter;"
        ))

    # ── Imprimir ──────────────────────────────────────────────────────────────

    def _print_report(self):
        """Abre el diálogo de impresión del sistema y envía el PDF."""
        if not self._pdf_path or not os.path.exists(self._pdf_path):
            QMessageBox.warning(self, "Error", "El PDF no está disponible.")
            return

        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))

        dlg = QPrintDialog(printer, self)
        dlg.setWindowTitle("Imprimir reporte")

        if dlg.exec() == QPrintDialog.Accepted:
            # Abrimos el PDF con el visor nativo del sistema (que soporta impresión)
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._pdf_path))

    # ── Exportar PDF ──────────────────────────────────────────────────────────

    def _export_pdf(self):
        """Guarda el PDF en la ubicación elegida por el usuario."""
        if not self._pdf_path or not os.path.exists(self._pdf_path):
            QMessageBox.warning(self, "Error", "El PDF no está disponible.")
            return

        fecha_str = self._data.get("fecha", "reporte").replace("-", "")
        default_name = f"reporte_ventas_{fecha_str}.pdf"

        dest, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar reporte como PDF",
            default_name,
            "Archivos PDF (*.pdf)"
        )

        if not dest:
            return  # usuario canceló

        try:
            shutil.copy2(self._pdf_path, dest)
            QMessageBox.information(
                self,
                "PDF exportado",
                f"El reporte se guardó correctamente en:\n{dest}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))

    # ── Limpieza ──────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        """Elimina el PDF temporal al cerrar el diálogo."""
        if self._pdf_path and os.path.exists(self._pdf_path):
            try:
                os.remove(self._pdf_path)
            except Exception:
                pass
        super().closeEvent(event)
