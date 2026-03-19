from datetime import date
from db.database import get_connection


class ReportManager:

    def get_daily_report(self, fecha: str = None):
        """
        Retorna todas las ventas del día indicado (por defecto hoy).

        fecha: string 'YYYY-MM-DD'. Si es None, usa la fecha actual.

        Retorna:
            {
                "success": True,
                "data": {
                    "fecha": "2025-01-15",
                    "ventas": [...],
                    "total_dia": 87500.0,
                    "num_ventas": 4
                }
            }
        """
        try:
            if fecha is None:
                fecha = date.today().strftime("%Y-%m-%d") # La fecha de hoy

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    v.id          AS venta_id,
                    v.fecha       AS fecha_hora,
                    v.total       AS total,
                    u.nombre      AS vendedor
                FROM ventas v
                JOIN usuarios u ON u.id = v.vendedor_id
                WHERE DATE(v.fecha) = ?
                ORDER BY v.fecha ASC
            """, (fecha,))

            rows = cursor.fetchall()

            ventas = []
            for row in rows:
                cursor.execute("""
                    SELECT
                        p.nombre       AS nombre,
                        dv.cantidad    AS cantidad,
                        dv.precio_unit AS precio_unit,
                        (dv.cantidad * dv.precio_unit) AS subtotal
                    FROM detalle_venta dv
                    JOIN productos p ON p.id = dv.producto_id
                    WHERE dv.venta_id = ?
                """, (row["venta_id"],))

                productos = [dict(d) for d in cursor.fetchall()]

                fecha_hora = row["fecha_hora"]
                hora = fecha_hora[11:19] if len(fecha_hora) >= 19 else fecha_hora

                ventas.append({
                    "venta_id":  row["venta_id"],
                    "hora":      hora,
                    "vendedor":  row["vendedor"],
                    "total":     row["total"],
                    "productos": productos,
                })

            total_dia = sum(v["total"] for v in ventas)

            conn.close()
            return {
                "success": True,
                "data": {
                    "fecha":      fecha,
                    "ventas":     ventas,
                    "total_dia":  total_dia,
                    "num_ventas": len(ventas),
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
