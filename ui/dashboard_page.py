from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, QDate, QMargins
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet,
    QBarCategoryAxis, QValueAxis
)
from modules.dashboard import DashboardManager

C_DARK   = "#1F3864"
C_BLUE   = "#2E86C1"
C_GREEN  = "#1E8449"
C_PURPLE = "#7D3C98"
C_ORANGE = "#D35400"
C_RED    = "#C0392B"
C_GOLD   = "#B7950B"
C_BG     = "#EAECF0"   # fondo gris de la página

BTN = """
    QPushButton {
        background-color: #2E86C1; color: white;
        border: none; border-radius: 6px;
        font-size: 12px; font-weight: bold; padding: 7px 16px;
    }
    QPushButton:hover   { background-color: #1A6FA3; }
    QPushButton:pressed { background-color: #145A87; }
"""

TBL = """
    QTableWidget {
        border: none; font-size: 12px;
        background-color: #FFFFFF;
        gridline-color: #F2F3F4;
    }
    QHeaderView::section {
        background-color: #FFFFFF;
        color: #999999;
        padding: 5px 8px;
        border: none;
        border-bottom: 1px solid #EAECF0;
        font-size: 10px;
        font-weight: bold;
    }
    QTableWidget::item {
        padding: 4px 8px;
        color: #333333;
        background-color: #FFFFFF;
    }
    QTableWidget::item:alternate { background-color: #F8F9FA; }
    QTableWidget::item:selected  { background-color: #D6EAF8; color: #1F3864; }
"""


def tcell(text, align=Qt.AlignLeft | Qt.AlignVCenter, bold=False, color=None):
    item = QTableWidgetItem(text)
    item.setTextAlignment(align)
    f = QFont()
    if bold: f.setBold(True)
    item.setFont(f)
    if color: item.setForeground(QColor(color))
    return item


def make_table(headers, col_widths):
    tbl = QTableWidget()
    tbl.setColumnCount(len(headers))
    tbl.setHorizontalHeaderLabels(headers)
    tbl.setStyleSheet(TBL)
    tbl.setEditTriggers(QTableWidget.NoEditTriggers)
    tbl.setSelectionBehavior(QTableWidget.SelectRows)
    tbl.verticalHeader().setVisible(False)
    tbl.setAlternatingRowColors(True)
    tbl.setShowGrid(False)
    tbl.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    tbl.verticalHeader().setDefaultSectionSize(34)
    for i, w in enumerate(col_widths):
        if w == 0:
            tbl.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)
        else:
            tbl.setColumnWidth(i, w)
    return tbl


class MetricCard(QWidget):
    """Tarjeta blanca con borde superior de color."""
    def __init__(self, icon, label, value, accent, subtitle="", parent=None):
        super().__init__(parent)
        # fondo explícitamente blanco
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: #FFFFFF;
                border-radius: 10px;
                border-top: 4px solid {accent};
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(100)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        top = QHBoxLayout()
        lbl_l = QLabel(label)
        lbl_l.setStyleSheet("color: #AAAAAA; font-size: 10px; font-weight: bold; letter-spacing: 0.5px; background-color: #FFFFFF;")
        lbl_l.setObjectName("mc_label")
        top.addWidget(lbl_l)
        top.addStretch()
        lbl_i = QLabel(icon)
        lbl_i.setStyleSheet("font-size: 18px; background-color: #FFFFFF;")
        top.addWidget(lbl_i)
        lay.addLayout(top)

        self.lbl_val = QLabel(value)
        self.lbl_val.setStyleSheet(f"color: #1A1A2E; font-size: 22px; font-weight: bold; background-color: #FFFFFF;")
        self.lbl_val.setWordWrap(True)
        lay.addWidget(self.lbl_val)

        self.lbl_sub = QLabel(subtitle)
        self.lbl_sub.setStyleSheet(f"color: {accent}; font-size: 11px; background-color: #FFFFFF;")
        self.lbl_sub.setObjectName("mc_sub")
        lay.addWidget(self.lbl_sub)

    def update_data(self, label, value, subtitle=""):
        self.findChild(QLabel, "mc_label").setText(label)
        self.lbl_val.setText(value)
        self.findChild(QLabel, "mc_sub").setText(subtitle)


class SmallCard(QWidget):
    """Tarjeta blanca compacta con borde izquierdo de color."""
    def __init__(self, icon, label, value, accent, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            SmallCard {{
                background-color: #FFFFFF;
                border-radius: 8px;
                border-left: 4px solid {accent};
            }}
        """)
        self.setFixedHeight(62)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(10)

        lbl_i = QLabel(icon)
        lbl_i.setStyleSheet("font-size: 20px; background-color: #FFFFFF;")
        lay.addWidget(lbl_i)

        info = QVBoxLayout()
        info.setSpacing(0)
        self.lbl_val = QLabel(value)
        self.lbl_val.setStyleSheet(f"color: {accent}; font-size: 17px; font-weight: bold; background-color: #FFFFFF;")
        lbl_l = QLabel(label)
        lbl_l.setStyleSheet("color: #AAAAAA; font-size: 10px; font-weight: bold; background-color: #FFFFFF;")
        info.addWidget(self.lbl_val)
        info.addWidget(lbl_l)
        lay.addLayout(info)
        lay.addStretch()

    def update_data(self, value):
        self.lbl_val.setText(value)


class PanelCard(QWidget):
    """Panel blanco con título y cuerpo."""
    def __init__(self, icon, title, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            PanelCard {
                background-color: #FFFFFF;
                border-radius: 10px;
            }
        """)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(14, 12, 14, 12)
        self._lay.setSpacing(8)

        lbl = QLabel(f"{icon}  {title}")
        lbl.setStyleSheet(f"color: #1F3864; font-size: 13px; font-weight: bold; background-color: #FFFFFF;")
        self._lay.addWidget(lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #EAECF0; background-color: #EAECF0; max-height: 1px;")
        self._lay.addWidget(sep)

    def body(self):
        return self._lay


class DashboardPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._manager = DashboardManager()
        # fondo gris de la página completa
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"DashboardPage {{ background-color: {C_BG}; }}")
        self._build_ui()
        self._load()

    def on_activated(self):
        self._load()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {C_BG}; border: none;")

        container = QWidget()
        container.setAttribute(Qt.WA_StyledBackground, True)
        container.setStyleSheet(f"background-color: {C_BG};")
        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        root = QVBoxLayout(container)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # ── Header ────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        ttl_row = QHBoxLayout(); ttl_row.setSpacing(8)
        ico = QLabel("📊"); ico.setStyleSheet("font-size: 20px;")
        ttl = QLabel("Métricas del Día")
        ttl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {C_DARK};")
        ttl_row.addWidget(ico); ttl_row.addWidget(ttl)
        hdr.addLayout(ttl_row)
        hdr.addStretch()

        fecha_str = QDate.currentDate().toString("dddd, dd 'de' MMMM yyyy").capitalize()
        lbl_fecha = QLabel(fecha_str)
        lbl_fecha.setStyleSheet("color: #888888; font-size: 12px; padding-right: 10px;")
        hdr.addWidget(lbl_fecha)

        self.lbl_comp = QLabel("Sin datos de ayer")
        self.lbl_comp.setStyleSheet("color: #888888; font-size: 12px; padding-right: 10px;")
        hdr.addWidget(self.lbl_comp)

        btn = QPushButton("🔄  Actualizar")
        btn.setStyleSheet(BTN)
        btn.clicked.connect(self._load)
        hdr.addWidget(btn)
        root.addLayout(hdr)

        # ── Fila 1: 4 tarjetas principales ───────────────────────────────
        r1 = QHBoxLayout(); r1.setSpacing(12)
        self.c_ingresos = MetricCard("💰", "INGRESOS DEL DÍA",    "$ 0", C_DARK,   "")
        self.c_trans    = MetricCard("🛒", "TRANSACCIONES",        "0",   C_GREEN,  "")
        self.c_prod     = MetricCard("🏆", "PROD. MÁS VENDIDO",   "—",   C_BLUE,   "")
        self.c_vend     = MetricCard("👤", "VENDEDOR TOP",         "—",   C_PURPLE, "")
        for c in [self.c_ingresos, self.c_trans, self.c_prod, self.c_vend]:
            r1.addWidget(c)
        root.addLayout(r1)

        # ── Fila 2: 3 tarjetas pequeñas de inventario ─────────────────────
        r2 = QHBoxLayout(); r2.setSpacing(12)
        self.s_bajo  = SmallCard("⚠️",  "PRODUCTOS STOCK BAJO", "0", C_GOLD)
        self.s_agot  = SmallCard("🚨",  "PRODUCTOS AGOTADOS",   "0", C_RED)
        self.s_total = SmallCard("📦",  "TOTAL EN INVENTARIO",  "0", C_ORANGE)
        for c in [self.s_bajo, self.s_agot, self.s_total]:
            r2.addWidget(c)
        r2.addStretch()
        root.addLayout(r2)

        # ── Fila 3: gráfico | top productos | stock bajo ──────────────────
        r3 = QHBoxLayout(); r3.setSpacing(12)

        p_chart = PanelCard("📈", "Ventas por hora")
        self.chart_view = self._make_chart()
        self.chart_view.setMinimumHeight(200)
        p_chart.body().addWidget(self.chart_view)
        r3.addWidget(p_chart, stretch=5)

        p_top = PanelCard("🏅", "Top productos del día")
        self.tbl_top = make_table(["Producto", "Cant.", "Ingreso"], [0, 50, 90])
        self.tbl_top.setFixedHeight(205)
        p_top.body().addWidget(self.tbl_top)
        r3.addWidget(p_top, stretch=3)

        p_stock = PanelCard("⚠️", "Stock bajo  (≤ 5 uds.)")
        self.tbl_stock = make_table(["Producto", "Stock"], [0, 65])
        self.tbl_stock.setFixedHeight(165)
        p_stock.body().addWidget(self.tbl_stock)
        self.lbl_ok = QLabel("✅  Todo en orden\nNo hay productos con stock bajo.")
        self.lbl_ok.setAlignment(Qt.AlignCenter)
        self.lbl_ok.setStyleSheet("color: #888888; font-size: 12px; padding: 16px;")
        self.lbl_ok.hide()
        p_stock.body().addWidget(self.lbl_ok)
        r3.addWidget(p_stock, stretch=3)

        root.addLayout(r3)

        # ── Fila 4: últimas ventas | por categoría ────────────────────────
        r4 = QHBoxLayout(); r4.setSpacing(12)

        p_ventas = PanelCard("🕐", "Últimas 5 ventas")
        self.tbl_ventas = make_table(["#", "Hora", "Vendedor", "Total"], [40, 55, 0, 105])
        self.tbl_ventas.setFixedHeight(195)
        p_ventas.body().addWidget(self.tbl_ventas)
        r4.addWidget(p_ventas, stretch=5)

        p_cat = PanelCard("📂", "Ventas por categoría")
        self.tbl_cat = make_table(["Categoría", "Uds.", "Ingreso"], [0, 55, 100])
        self.tbl_cat.setFixedHeight(195)
        p_cat.body().addWidget(self.tbl_cat)
        r4.addWidget(p_cat, stretch=4)

        root.addLayout(r4)

    def _make_chart(self):
        self._chart = QChart()
        self._chart.setBackgroundVisible(False)
        self._chart.setMargins(QMargins(0, 4, 0, 0))
        self._chart.legend().hide()
        self._chart.setAnimationOptions(QChart.SeriesAnimations)
        view = QChartView(self._chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setBackgroundBrush(QColor("#FFFFFF"))
        view.setStyleSheet("background-color: #FFFFFF; border: none;")
        return view

    def _load(self):
        result = self._manager.get_daily_metrics()
        if not result["success"]:
            return
        d = result["data"]

        # Tarjetas
        pct_vend = ""
        if d["total_ingresos"] > 0 and d["vendedor_top"]["total"] > 0:
            pct = (d["vendedor_top"]["total"] / d["total_ingresos"]) * 100
            pct_vend = f"{pct:.0f}% de ventas hoy"

        self.c_ingresos.update_data("INGRESOS DEL DÍA",   f"$ {d['total_ingresos']:,.0f}")
        self.c_trans.update_data("TRANSACCIONES",           str(d["num_transacciones"]))
        self.c_prod.update_data(
            "PROD. MÁS VENDIDO",
            d["producto_mas_vendido"]["nombre"],
            f"{d['producto_mas_vendido']['cantidad']} unidades" if d["producto_mas_vendido"]["cantidad"] else ""
        )
        self.c_vend.update_data("VENDEDOR TOP", d["vendedor_top"]["nombre"], pct_vend)

        self.s_bajo.update_data(str(len(d["stock_bajo"])))
        self.s_agot.update_data(str(d["productos_agotados"]))
        self.s_total.update_data(str(d["total_productos"]))

        # Comparativo
        ayer = d["ingresos_ayer"]; hoy = d["total_ingresos"]
        if ayer > 0:
            pct = ((hoy - ayer) / ayer) * 100
            s = "▲" if pct >= 0 else "▼"
            col = C_GREEN if pct >= 0 else C_RED
            self.lbl_comp.setText(
                f'<span style="color:{col};font-weight:bold;">{s} {abs(pct):.1f}%</span> vs ayer'
            )
        else:
            self.lbl_comp.setText("Sin datos de ayer")

        # Gráfico
        self._update_chart(d["ventas_por_hora"])

        # Top productos
        self.tbl_top.setRowCount(0)
        for p in d["top_productos"]:
            r = self.tbl_top.rowCount(); self.tbl_top.insertRow(r)
            self.tbl_top.setItem(r, 0, tcell(p["nombre"]))
            self.tbl_top.setItem(r, 1, tcell(str(p["cantidad"]), Qt.AlignCenter, bold=True, color=C_BLUE))
            self.tbl_top.setItem(r, 2, tcell(f"$ {p['monto']:,.0f}", Qt.AlignRight | Qt.AlignVCenter, bold=True, color=C_GREEN))

        # Stock bajo
        self.tbl_stock.setRowCount(0)
        if d["stock_bajo"]:
            self.tbl_stock.show(); self.lbl_ok.hide()
            for p in d["stock_bajo"]:
                r = self.tbl_stock.rowCount(); self.tbl_stock.insertRow(r)
                self.tbl_stock.setItem(r, 0, tcell(p["nombre"]))
                col = C_RED if p["cantidad"] == 0 else C_GOLD
                lbl = "AGOTADO" if p["cantidad"] == 0 else str(p["cantidad"])
                self.tbl_stock.setItem(r, 1, tcell(lbl, Qt.AlignCenter, bold=True, color=col))
        else:
            self.tbl_stock.hide(); self.lbl_ok.show()

        # Últimas ventas
        self.tbl_ventas.setRowCount(0)
        for v in d["ultimas_ventas"]:
            r = self.tbl_ventas.rowCount(); self.tbl_ventas.insertRow(r)
            self.tbl_ventas.setItem(r, 0, tcell(f"#{v['venta_id']}", Qt.AlignCenter, color="#AAAAAA"))
            self.tbl_ventas.setItem(r, 1, tcell(v["hora"], Qt.AlignCenter))
            self.tbl_ventas.setItem(r, 2, tcell(v["vendedor"]))
            self.tbl_ventas.setItem(r, 3, tcell(f"$ {v['total']:,.0f}", Qt.AlignRight | Qt.AlignVCenter, bold=True, color=C_GREEN))

        # Por categoría
        self.tbl_cat.setRowCount(0)
        for c in d["ventas_por_categoria"]:
            r = self.tbl_cat.rowCount(); self.tbl_cat.insertRow(r)
            self.tbl_cat.setItem(r, 0, tcell(c["categoria"]))
            self.tbl_cat.setItem(r, 1, tcell(str(c["cantidad"]), Qt.AlignCenter))
            self.tbl_cat.setItem(r, 2, tcell(f"$ {c['monto']:,.0f}", Qt.AlignRight | Qt.AlignVCenter, bold=True, color=C_DARK))

    def _update_chart(self, ventas_por_hora: dict):
        self._chart.removeAllSeries()
        for ax in self._chart.axes():
            self._chart.removeAxis(ax)
        if not ventas_por_hora:
            return

        bar_set = QBarSet("")
        bar_set.setColor(QColor(C_BLUE))
        bar_set.setBorderColor(QColor(C_BLUE))
        horas = sorted(ventas_por_hora.keys())
        for h in horas:
            bar_set.append(ventas_por_hora[h]["qty"])

        series = QBarSeries()
        series.append(bar_set)
        series.setBarWidth(0.4)
        self._chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append([f"{h}:00" for h in horas])
        axis_x.setLabelsColor(QColor("#888888"))
        self._chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        max_val = max(v["qty"] for v in ventas_por_hora.values())
        axis_y = QValueAxis()
        axis_y.setLabelFormat("%d")
        axis_y.setRange(0, max_val + 1)
        axis_y.setTickCount(min(max_val + 2, 6))
        axis_y.setLabelsColor(QColor("#888888"))
        axis_y.setGridLineColor(QColor("#EAECF0"))
        axis_y.setLinePenColor(QColor("#EAECF0"))
        self._chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
