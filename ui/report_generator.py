"""
report_generator.py
Genera el PDF del reporte diario de ventas usando ReportLab.
Uso:
    path = ReportGenerator.build(data)   # retorna ruta del archivo generado
"""

import os
import tempfile
from datetime import datetime
from collections import defaultdict

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


# ── Paleta de colores del POS ──────────────────────────────────────────────────
COLOR_DARK   = colors.HexColor("#1F3864")   # Azul oscuro (encabezados)
COLOR_MID    = colors.HexColor("#2E5FA3")   # Azul medio
COLOR_GREEN  = colors.HexColor("#1E8449")   # Verde (totales)
COLOR_LIGHT  = colors.HexColor("#D6EAF8")   # Azul muy claro (filas alternas)
COLOR_GRAY   = colors.HexColor("#F2F3F4")   # Gris claro
COLOR_TEXT   = colors.HexColor("#1C2833")   # Texto principal


class ReportGenerator:

    @staticmethod
    def build(data: dict, output_path: str = None) -> str:
        """
        Construye el PDF del reporte diario.

        data: dict retornado por ReportManager.get_daily_report()["data"]
              {
                  "fecha": "2025-03-18",
                  "ventas": [...],
                  "total_dia": 87500.0,
                  "num_ventas": 4
              }

        output_path: ruta donde guardar el PDF. Si es None, usa un temp file.

        Retorna la ruta del PDF generado.
        """
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".pdf", prefix="reporte_ventas_")
            os.close(fd)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        story = ReportGenerator._build_story(data)
        doc.build(story, onFirstPage=ReportGenerator._add_page_footer,
                  onLaterPages=ReportGenerator._add_page_footer)

        return output_path

    # ── Construcción del contenido ─────────────────────────────────────────────

    @staticmethod
    def _build_story(data: dict) -> list:
        styles = ReportGenerator._get_styles()
        story  = []

        fecha      = data["fecha"]
        ventas     = data["ventas"]
        total_dia  = data["total_dia"]
        num_ventas = data["num_ventas"]

        fecha_fmt = ReportGenerator._fmt_fecha(fecha)

        # ── Encabezado ─────────────────────────────────────────────────────────
        story.append(Paragraph("EMPRESA XYZ", styles["titulo_empresa"]))
        story.append(Paragraph("Mini-Sistema POS", styles["subtitulo_empresa"]))
        story.append(Spacer(1, 0.3 * cm))
        story.append(HRFlowable(width="100%", thickness=2, color=COLOR_DARK))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("REPORTE DIARIO DE VENTAS", styles["titulo_reporte"]))
        story.append(Paragraph(f"Fecha: {fecha_fmt}", styles["fecha_reporte"]))
        story.append(Paragraph(
            f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}",
            styles["meta_reporte"]
        ))
        story.append(Spacer(1, 0.6 * cm))

        # ── Tarjetas de resumen ────────────────────────────────────────────────
        resumen_data = [
            ["Transacciones del día", "Total de ingresos"],
            [str(num_ventas), f"$ {total_dia:,.0f}"],
        ]
        resumen_table = Table(resumen_data, colWidths=[8.5 * cm, 8.5 * cm])
        resumen_table.setStyle(TableStyle([
            # Fila de encabezado
            ("BACKGROUND",   (0, 0), (-1, 0), COLOR_DARK),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 10),
            ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
            ("BOTTOMPADDING",(0, 0), (-1, 0), 8),
            ("TOPPADDING",   (0, 0), (-1, 0), 8),
            # Fila de valores
            ("BACKGROUND",   (0, 1), (-1, 1), COLOR_LIGHT),
            ("FONTNAME",     (0, 1), (-1, 1), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 1), (-1, 1), 18),
            ("ALIGN",        (0, 1), (-1, 1), "CENTER"),
            ("TEXTCOLOR",    (0, 1), (0, 1),  COLOR_DARK),
            ("TEXTCOLOR",    (1, 1), (1, 1),  COLOR_GREEN),
            ("TOPPADDING",   (0, 1), (-1, 1), 10),
            ("BOTTOMPADDING",(0, 1), (-1, 1), 10),
            ("BOX",          (0, 0), (-1, -1), 1, COLOR_MID),
            ("INNERGRID",    (0, 0), (-1, -1), 0.5, COLOR_MID),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("ROUNDEDCORNERS", [4]),
        ]))
        story.append(resumen_table)
        story.append(Spacer(1, 0.7 * cm))

        # ── Sin ventas ─────────────────────────────────────────────────────────
        if not ventas:
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_MID))
            story.append(Spacer(1, 0.5 * cm))
            story.append(Paragraph(
                "No se registraron ventas durante el día de hoy.",
                styles["sin_ventas"]
            ))
            story.append(Spacer(1, 0.3 * cm))
            story.append(Paragraph(
                "El cierre de caja no presenta movimientos.",
                styles["sin_ventas_sub"]
            ))
            return story

        # ── Tabla de ventas ────────────────────────────────────────────────────
        story.append(Paragraph("Detalle de transacciones", styles["seccion"]))
        story.append(Spacer(1, 0.2 * cm))

        encabezados = ["#", "Hora", "Vendedor", "Productos", "Monto"]
        filas = [encabezados]

        from reportlab.platypus import Paragraph as P
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_LEFT
        prod_style = ParagraphStyle(
            "prod_cell", fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor("#1C2833"), leading=11,
            alignment=TA_LEFT
        )
        for v in ventas:
            productos_str = ReportGenerator._resumir_productos(v["productos"])
            filas.append([
                f"#{v['venta_id']}",
                v["hora"],
                v["vendedor"],
                P(productos_str, prod_style),
                f"$ {v['total']:,.0f}",
            ])

        col_widths = [1.2 * cm, 1.8 * cm, 3.5 * cm, 7.5 * cm, 3 * cm]
        ventas_table = Table(filas, colWidths=col_widths, repeatRows=1)

        row_styles = [
            # Encabezado
            ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  9),
            ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
            ("TOPPADDING",    (0, 0), (-1, 0),  7),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  7),
            # Datos
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 1), (-1, -1), 8),
            ("TOPPADDING",    (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            # Columnas alineadas
            ("ALIGN",         (0, 1), (0, -1),  "CENTER"),   # #
            ("ALIGN",         (1, 1), (1, -1),  "CENTER"),   # hora
            ("ALIGN",         (4, 1), (4, -1),  "RIGHT"),    # monto
            ("FONTNAME",      (4, 1), (4, -1),  "Helvetica-Bold"),
            ("TEXTCOLOR",     (4, 1), (4, -1),  COLOR_GREEN),
            # Bordes
            ("BOX",           (0, 0), (-1, -1), 1,   COLOR_MID),
            ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#D5D8DC")),
        ]

        # Filas alternas
        for i in range(1, len(filas)):
            if i % 2 == 0:
                row_styles.append(("BACKGROUND", (0, i), (-1, i), COLOR_GRAY))

        ventas_table.setStyle(TableStyle(row_styles))
        story.append(ventas_table)
        story.append(Spacer(1, 0.3 * cm))

        # ── Total final ────────────────────────────────────────────────────────
        total_data = [
            ["", "", "", "TOTAL DEL DÍA:", f"$ {total_dia:,.0f}"],
        ]
        total_table = Table(total_data, colWidths=col_widths)
        total_table.setStyle(TableStyle([
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0), 10),
            ("ALIGN",         (3, 0), (3, 0),  "RIGHT"),
            ("ALIGN",         (4, 0), (4, 0),  "RIGHT"),
            ("TEXTCOLOR",     (3, 0), (3, 0),  COLOR_DARK),
            ("TEXTCOLOR",     (4, 0), (4, 0),  COLOR_GREEN),
            ("FONTSIZE",      (4, 0), (4, 0),  12),
            ("TOPPADDING",    (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("LINEABOVE",     (0, 0), (-1, 0), 1.5, COLOR_DARK),
        ]))
        story.append(total_table)
        story.append(Spacer(1, 0.8 * cm))

        # ── Desglose por vendedor (si hay más de uno) ──────────────────────────
        vendedores = defaultdict(lambda: {"total": 0.0, "num": 0})
        for v in ventas:
            vendedores[v["vendedor"]]["total"] += v["total"]
            vendedores[v["vendedor"]]["num"]   += 1

        if len(vendedores) > 1:
            story.append(HRFlowable(width="100%", thickness=1, color=COLOR_MID))
            story.append(Spacer(1, 0.4 * cm))
            story.append(Paragraph("Desglose por vendedor", styles["seccion"]))
            story.append(Spacer(1, 0.2 * cm))

            dv_data = [["Vendedor", "Transacciones", "Total vendido"]]
            for nombre, stats in sorted(vendedores.items()):
                dv_data.append([
                    nombre,
                    str(stats["num"]),
                    f"$ {stats['total']:,.0f}",
                ])

            dv_table = Table(dv_data, colWidths=[9 * cm, 4 * cm, 4 * cm])
            dv_table.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0),  COLOR_MID),
                ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
                ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
                ("FONTSIZE",      (0, 0), (-1, 0),  9),
                ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
                ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE",      (0, 1), (-1, -1), 9),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TEXTCOLOR",     (2, 1), (2, -1),  COLOR_GREEN),
                ("FONTNAME",      (2, 1), (2, -1),  "Helvetica-Bold"),
                ("BOX",           (0, 0), (-1, -1), 1,   COLOR_MID),
                ("INNERGRID",     (0, 0), (-1, -1), 0.3, colors.HexColor("#D5D8DC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_GRAY]),
            ]))
            story.append(dv_table)
            story.append(Spacer(1, 0.5 * cm))

        # ── Firma / cierre ─────────────────────────────────────────────────────
        story.append(HRFlowable(width="100%", thickness=1, color=COLOR_MID))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Documento generado automáticamente por Mini-Sistema POS", styles["pie"]))

        return story

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _resumir_productos(productos: list) -> str:
        """Convierte la lista de productos en líneas separadas para mostrar todos."""
        if not productos:
            return "—"
        partes = [f"{p['nombre']} ×{p['cantidad']}" for p in productos]
        return "<br/>".join(partes)

    @staticmethod
    def _fmt_fecha(fecha_iso: str) -> str:
        """Convierte '2025-03-18' → 'martes, 18 de marzo de 2025'."""
        meses = [
            "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
        ]
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        try:
            dt = datetime.strptime(fecha_iso, "%Y-%m-%d")
            return f"{dias[dt.weekday()]}, {dt.day} de {meses[dt.month]} de {dt.year}"
        except Exception:
            return fecha_iso

    @staticmethod
    def _add_page_footer(canvas, doc):
        """Pie de página con número de página."""
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawRightString(
            doc.pagesize[0] - 2 * cm,
            1.2 * cm,
            f"Página {doc.page}"
        )
        canvas.drawString(
            2 * cm,
            1.2 * cm,
            "Mini-Sistema POS — Reporte Diario de Ventas"
        )
        canvas.restoreState()

    @staticmethod
    def _get_styles() -> dict:
        base = getSampleStyleSheet()

        def s(name, **kwargs):
            return ParagraphStyle(name, parent=base["Normal"], **kwargs)

        return {
            "titulo_empresa": s(
                "titulo_empresa",
                fontSize=18, fontName="Helvetica-Bold",
                textColor=COLOR_DARK, alignment=TA_CENTER, spaceAfter=10
            ),
            "subtitulo_empresa": s(
                "subtitulo_empresa",
                fontSize=11, fontName="Helvetica",
                textColor=COLOR_MID, alignment=TA_CENTER, spaceAfter=4
            ),
            "titulo_reporte": s(
                "titulo_reporte",
                fontSize=14, fontName="Helvetica-Bold",
                textColor=COLOR_DARK, alignment=TA_CENTER, spaceAfter=4
            ),
            "fecha_reporte": s(
                "fecha_reporte",
                fontSize=11, fontName="Helvetica-Bold",
                textColor=COLOR_MID, alignment=TA_CENTER, spaceAfter=2
            ),
            "meta_reporte": s(
                "meta_reporte",
                fontSize=8, fontName="Helvetica",
                textColor=colors.HexColor("#888"), alignment=TA_CENTER, spaceAfter=2
            ),
            "seccion": s(
                "seccion",
                fontSize=11, fontName="Helvetica-Bold",
                textColor=COLOR_DARK, spaceAfter=4
            ),
            "sin_ventas": s(
                "sin_ventas",
                fontSize=13, fontName="Helvetica-Bold",
                textColor=colors.HexColor("#888"), alignment=TA_CENTER, spaceAfter=6
            ),
            "sin_ventas_sub": s(
                "sin_ventas_sub",
                fontSize=10, fontName="Helvetica",
                textColor=colors.HexColor("#AAA"), alignment=TA_CENTER
            ),
            "pie": s(
                "pie",
                fontSize=8, fontName="Helvetica",
                textColor=colors.HexColor("#888"), alignment=TA_CENTER, spaceAfter=2
            ),
        }
