from datetime import datetime
from db.database import get_connection


class SalesManager:

    def create_sale(self, vendedor_id, items):
        """
        Registra una venta completa con sus productos.

        items es una lista de diccionarios con este formato:
        [
            {"producto_id": 1, "cantidad": 2, "precio_unit": 5000},
            {"producto_id": 3, "cantidad": 1, "precio_unit": 12000},
        ]

        Este método debe:
        - Calcular el total sumando cantidad * precio_unit de cada item
        - Insertar la venta en la tabla ventas
        - Insertar cada item en detalle_venta
        - Llamar a InventoryManager.discount_stock por cada producto

        Retorna: {"success": True, "data": venta_id} o {"success": False, "error": "..."}
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            # 1. Verificar stock suficiente antes de hacer cualquier cambio
            for item in items:
                cursor.execute(
                    "SELECT cantidad, nombre FROM productos WHERE id = ?",
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

            # 2. Calcular total
            total = sum(item["cantidad"] * item["precio_unit"] for item in items)
            fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 3. Insertar cabecera de la venta
            cursor.execute(
                "INSERT INTO ventas (vendedor_id, total, fecha) VALUES (?, ?, ?)",
                (vendedor_id, total, fecha)
            )
            venta_id = cursor.lastrowid

            # 4. Insertar detalle y descontar stock (todo en la misma transacción)
            for item in items:
                cursor.execute(
                    "INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unit) "
                    "VALUES (?, ?, ?, ?)",
                    (venta_id, item["producto_id"], item["cantidad"], item["precio_unit"])
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
        pass