from db.database import get_connection


class InventoryManager:

    def get_all(self):
        """
        Retorna todos los productos del inventario.
        Retorna: {"success": True, "data": [lista de productos]}
        """
        pass

    def get_by_id(self, producto_id):
        """
        Retorna un producto por su ID.
        Retorna: {"success": True, "data": producto} o {"success": False, "error": "..."}
        """
        pass

    def add(self, nombre, precio, cantidad, categoria=None):
        """
        Agrega un nuevo producto al inventario.
        Retorna: {"success": True, "data": None} o {"success": False, "error": "..."}
        """
        pass

    def update(self, producto_id, nombre, precio, cantidad, categoria=None):
        """
        Edita un producto existente.
        Retorna: {"success": True, "data": None} o {"success": False, "error": "..."}
        """
        pass

    def delete(self, producto_id):
        """
        Elimina un producto por su ID.
        Retorna: {"success": True, "data": None} o {"success": False, "error": "..."}
        """
        pass

    def discount_stock(self, producto_id, cantidad):
        """
        Descuenta cantidad del stock de un producto al registrar una venta.
        Retorna: {"success": True, "data": None} o {"success": False, "error": "..."}
        """
        pass