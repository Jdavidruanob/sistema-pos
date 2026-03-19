from datetime import datetime

from config import APP_NAME
from db.database import get_connection


class SalesManager:

    def _build_sale_payload(self, cursor, venta_id):
        cursor.execute("""
            SELECT
                v.id          AS venta_id,
                v.fecha       AS fecha_hora,
                v.total       AS total,
                u.id          AS vendedor_id,
                u.nombre      AS vendedor
            FROM ventas v
            JOIN usuarios u ON u.id = v.vendedor_id
            WHERE v.id = ?
        """, (venta_id,))
        sale = cursor.fetchone()

        if not sale:
            return None

        cursor.execute("""
            SELECT
                dv.producto_id              AS producto_id,
                p.nombre                    AS nombre,
                dv.cantidad                 AS cantidad,
                dv.precio_unit              AS precio_unit,
                dv.descuento_monto          AS descuento_monto,
                (dv.cantidad * dv.precio_unit) AS subtotal_bruto,
                (dv.cantidad * dv.precio_unit - dv.descuento_monto) AS subtotal
            FROM detalle_venta dv
            JOIN productos p ON p.id = dv.producto_id
            WHERE dv.venta_id = ?
            ORDER BY dv.id ASC
        """, (venta_id,))

        items = []
        total_descuentos = 0.0
        for row in cursor.fetchall():
            item = dict(row)
            item["precio_original"] = item["precio_unit"]
            total_descuentos += item["descuento_monto"]
            items.append(item)

        return {
            "venta_id": sale["venta_id"],
            "numero_transaccion": f"#{sale['venta_id']}",
            "negocio": APP_NAME,
            "fecha_hora": sale["fecha_hora"],
            "vendedor_id": sale["vendedor_id"],
            "vendedor": sale["vendedor"],
            "items": items,
            "subtotal": sum(item.get("subtotal_bruto", item.get("subtotal", 0)) for item in items),
            "total_descuentos": total_descuentos,
            "total": sale["total"],
        }

    def create_sale(self, vendedor_id, items):
        """
        Registra una venta completa con sus productos.

        items es una lista de diccionarios con este formato:
        [
            {"producto_id": 1, "cantidad": 2},
            {"producto_id": 3, "cantidad": 1},
        ]

        Este método:
        - Verifica stock suficiente antes de hacer cambios
        - Obtiene precio base y descuento vigente del producto
        - Calcula el total sumando cantidad * precio_base - descuentos
        - Inserta la venta en la tabla ventas
        - Inserta cada item con descuento_monto en detalle_venta
        - Descuenta stock

        Retorna: {"success": True, "data": venta_id} o {"success": False, "error": "..."}
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 1. Verificar stock y obtener información de descuentos de cada producto
            items_con_descuento = []
            total = 0.0
            
            for item in items:
                cursor.execute(
                    """
                    SELECT cantidad, nombre, precio, descuento_pct, descuento_activo
                    FROM productos WHERE id = ?
                    """,
                    (item["producto_id"],)
                )
                producto = cursor.fetchone()

                if not producto:
                    conn.close()
                    return {"success": False, "error": f"Producto con id {item['producto_id']} no encontrado"}

                if producto["cantidad"] < item["cantidad"]:
                    conn.close()
                    return {
                        "success": False,
                        "error": f"Stock insuficiente para '{producto['nombre']}': "
                                 f"disponible {producto['cantidad']}, solicitado {item['cantidad']}"
                    }

                precio_base = producto["precio"]
                subtotal_bruto = item["cantidad"] * precio_base

                # Calcular descuento si está activo
                descuento_monto = 0.0
                if producto["descuento_activo"] and producto["descuento_pct"] > 0:
                    descuento_monto = subtotal_bruto * (producto["descuento_pct"] / 100.0)
                
                subtotal_con_descuento = subtotal_bruto - descuento_monto
                total += subtotal_con_descuento

                items_con_descuento.append({
                    "producto_id": item["producto_id"],
                    "cantidad": item["cantidad"],
                    "precio_unit": precio_base,
                    "descuento_monto": descuento_monto,
                })

            # 2. Insertar cabecera de la venta
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO ventas (vendedor_id, total, fecha) VALUES (?, ?, ?)",
                (vendedor_id, total, fecha)
            )
            venta_id = cursor.lastrowid

            # 3. Insertar detalle y descontar stock
            for item in items_con_descuento:
                cursor.execute(
                    """
                    INSERT INTO detalle_venta 
                    (venta_id, producto_id, cantidad, precio_unit, descuento_monto) 
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (venta_id, item["producto_id"], item["cantidad"], 
                     item["precio_unit"], item["descuento_monto"])
                )
                cursor.execute(
                    "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
                    (item["cantidad"], item["producto_id"])
                )

            conn.commit()
            conn.close()
            return {"success": True, "data": venta_id}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_sale(self, venta_id):
        """
        Retorna el detalle completo de una venta por su ID,
        incluyendo los productos vendidos.

        Retorna: {"success": True, "data": venta_con_detalle} o {"success": False, "error": "..."}
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            sale = self._build_sale_payload(cursor, venta_id)
            conn.close()

            if not sale:
                return {"success": False, "error": "Venta no encontrada"}

            return {"success": True, "data": sale}

        except Exception as e:
            return {"success": False, "error": str(e)}
