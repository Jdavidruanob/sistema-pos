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
        pass

    def get_sale(self, venta_id):
        """
        Retorna el detalle completo de una venta por su ID,
        incluyendo los productos vendidos.

        Retorna: {"success": True, "data": venta_con_detalle} o {"success": False, "error": "..."}
        """
        pass