from datetime import date, timedelta
from db.database import get_connection


class DashboardManager:

    def get_daily_metrics(self, fecha: str = None):
        try:
            if fecha is None:
                fecha = date.today().strftime("%Y-%m-%d")
            ayer = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

            conn = get_connection()
            cursor = conn.cursor()

            # ── Ingresos y transacciones del día ──────────────────────────
            cursor.execute("""
                SELECT COUNT(*) AS num, COALESCE(SUM(total), 0) AS total
                FROM ventas WHERE DATE(fecha) = ?
            """, (fecha,))
            row = cursor.fetchone()
            num_transacciones = row["num"]
            total_ingresos    = row["total"]

            # ── Ingresos de ayer ──────────────────────────────────────────
            cursor.execute("""
                SELECT COALESCE(SUM(total), 0) AS total
                FROM ventas WHERE DATE(fecha) = ?
            """, (ayer,))
            ingresos_ayer = cursor.fetchone()["total"]

            # ── Producto más vendido ──────────────────────────────────────
            cursor.execute("""
                SELECT p.nombre, SUM(dv.cantidad) AS total_qty
                FROM detalle_venta dv
                JOIN ventas v    ON v.id = dv.venta_id
                JOIN productos p ON p.id = dv.producto_id
                WHERE DATE(v.fecha) = ?
                GROUP BY dv.producto_id
                ORDER BY total_qty DESC LIMIT 1
            """, (fecha,))
            row_prod = cursor.fetchone()
            producto_mas_vendido = (
                {"nombre": row_prod["nombre"], "cantidad": row_prod["total_qty"]}
                if row_prod else {"nombre": "—", "cantidad": 0}
            )

            # ── Vendedor top ──────────────────────────────────────────────
            cursor.execute("""
                SELECT u.nombre, COALESCE(SUM(v.total), 0) AS total_vendido
                FROM ventas v
                JOIN usuarios u ON u.id = v.vendedor_id
                WHERE DATE(v.fecha) = ?
                GROUP BY v.vendedor_id
                ORDER BY total_vendido DESC LIMIT 1
            """, (fecha,))
            row_vend = cursor.fetchone()
            vendedor_top = (
                {"nombre": row_vend["nombre"], "total": row_vend["total_vendido"]}
                if row_vend else {"nombre": "—", "total": 0.0}
            )

            # ── Últimas 5 ventas ──────────────────────────────────────────
            cursor.execute("""
                SELECT v.id AS venta_id, v.fecha, v.total, u.nombre AS vendedor
                FROM ventas v
                JOIN usuarios u ON u.id = v.vendedor_id
                WHERE DATE(v.fecha) = ?
                ORDER BY v.fecha DESC LIMIT 5
            """, (fecha,))
            ultimas_ventas = []
            for r in cursor.fetchall():
                hora = r["fecha"][11:16] if len(r["fecha"]) >= 16 else r["fecha"]
                ultimas_ventas.append({
                    "venta_id": r["venta_id"],
                    "hora":     hora,
                    "vendedor": r["vendedor"],
                    "total":    r["total"],
                })

            # ── Ventas por hora ───────────────────────────────────────────
            cursor.execute("""
                SELECT strftime('%H', fecha) AS hora,
                       COUNT(*) AS qty,
                       COALESCE(SUM(total), 0) AS monto
                FROM ventas WHERE DATE(fecha) = ?
                GROUP BY hora ORDER BY hora ASC
            """, (fecha,))
            ventas_por_hora = {}
            for r in cursor.fetchall():
                ventas_por_hora[r["hora"]] = {"qty": r["qty"], "monto": r["monto"]}

            # ── Top 5 productos más vendidos del día ──────────────────────
            cursor.execute("""
                SELECT p.nombre, p.categoria,
                       SUM(dv.cantidad) AS total_qty,
                       SUM(dv.cantidad * dv.precio_unit) AS total_monto
                FROM detalle_venta dv
                JOIN ventas v    ON v.id = dv.venta_id
                JOIN productos p ON p.id = dv.producto_id
                WHERE DATE(v.fecha) = ?
                GROUP BY dv.producto_id
                ORDER BY total_qty DESC LIMIT 5
            """, (fecha,))
            top_productos = [
                {"nombre": r["nombre"], "categoria": r["categoria"] or "—",
                 "cantidad": r["total_qty"], "monto": r["total_monto"]}
                for r in cursor.fetchall()
            ]

            # ── Ventas por categoría ──────────────────────────────────────
            cursor.execute("""
                SELECT p.categoria,
                       SUM(dv.cantidad) AS total_qty,
                       SUM(dv.cantidad * dv.precio_unit) AS total_monto
                FROM detalle_venta dv
                JOIN ventas v    ON v.id = dv.venta_id
                JOIN productos p ON p.id = dv.producto_id
                WHERE DATE(v.fecha) = ?
                GROUP BY p.categoria
                ORDER BY total_monto DESC
            """, (fecha,))
            ventas_por_categoria = [
                {"categoria": r["categoria"] or "Sin categoría",
                 "cantidad": r["total_qty"], "monto": r["total_monto"]}
                for r in cursor.fetchall()
            ]

            # ── Stock bajo (≤ 5 unidades) ─────────────────────────────────
            cursor.execute("""
                SELECT nombre, cantidad, categoria
                FROM productos
                WHERE cantidad <= 5
                ORDER BY cantidad ASC
            """)
            stock_bajo = [
                {"nombre": r["nombre"], "cantidad": r["cantidad"],
                 "categoria": r["categoria"] or "—"}
                for r in cursor.fetchall()
            ]

            # ── Productos agotados y total inventario ─────────────────────
            cursor.execute("SELECT COUNT(*) AS n FROM productos WHERE cantidad = 0")
            productos_agotados = cursor.fetchone()["n"]

            cursor.execute("SELECT COUNT(*) AS n FROM productos")
            total_productos = cursor.fetchone()["n"]

            conn.close()
            return {
                "success": True,
                "data": {
                    "fecha":                fecha,
                    "total_ingresos":       total_ingresos,
                    "num_transacciones":    num_transacciones,
                    "producto_mas_vendido": producto_mas_vendido,
                    "vendedor_top":         vendedor_top,
                    "ultimas_ventas":       ultimas_ventas,
                    "ventas_por_hora":      ventas_por_hora,
                    "ingresos_ayer":        ingresos_ayer,
                    "top_productos":        top_productos,
                    "ventas_por_categoria": ventas_por_categoria,
                    "stock_bajo":           stock_bajo,
                    "productos_agotados":   productos_agotados,
                    "total_productos":      total_productos,
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
