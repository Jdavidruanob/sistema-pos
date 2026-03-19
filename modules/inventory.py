from db.database import get_connection


class InventoryManager:

    def get_all(self):
        """
        Retorna todos los productos del inventario.
        Retorna: {"success": True, "data": [lista de productos]}
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    id, nombre, precio, cantidad, categoria, 
                    descuento_pct, descuento_activo
                FROM productos 
                ORDER BY nombre
            """)
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return {"success": True, "data": rows}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_by_id(self, producto_id):
        """
        Retorna un producto por su ID.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, nombre, precio, cantidad, categoria, 
                       descuento_pct, descuento_activo 
                FROM productos 
                WHERE id = ?
                """,
                (producto_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return {"success": False, "error": "Producto no encontrado"}

            return {"success": True, "data": dict(row)}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def add(self, nombre, precio, cantidad, categoria=None):
        """
        Agrega un nuevo producto al inventario.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO productos (nombre, precio, cantidad, categoria) VALUES (?, ?, ?, ?)",
                (nombre, precio, cantidad, categoria)
            )

            conn.commit()
            conn.close()

            return {"success": True, "data": None}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update(self, producto_id, nombre, precio, cantidad, categoria=None):
        """
        Edita un producto existente.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE productos
                SET nombre = ?, precio = ?, cantidad = ?, categoria = ?
                WHERE id = ?
                """,
                (nombre, precio, cantidad, categoria, producto_id)
            )

            if cursor.rowcount == 0:
                conn.close()
                return {"success": False, "error": "Producto no encontrado"}

            conn.commit()
            conn.close()

            return {"success": True, "data": None}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete(self, producto_id):
        """
        Elimina un producto por su ID.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))

            if cursor.rowcount == 0:
                conn.close()
                return {"success": False, "error": "Producto no encontrado"}

            conn.commit()
            conn.close()

            return {"success": True, "data": None}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def discount_stock(self, producto_id, cantidad):
        """
        Descuenta cantidad del stock de un producto al registrar una venta.
        """
        try:
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT cantidad FROM productos WHERE id = ?", (producto_id,))
            producto = cursor.fetchone()

            if not producto:
                conn.close()
                return {"success": False, "error": f"Producto {producto_id} no encontrado"}

            if producto["cantidad"] < cantidad:
                conn.close()
                return {"success": False, "error": "Stock insuficiente"}

            cursor.execute(
                "UPDATE productos SET cantidad = cantidad - ? WHERE id = ?",
                (cantidad, producto_id)
            )

            conn.commit()
            conn.close()
            return {"success": True, "data": None}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_discount(self, producto_id, descuento_pct, descuento_activo):
        """
        Configura el descuento de un producto.
        
        descuento_pct: porcentaje de descuento (ej: 10 para 10%)
        descuento_activo: 1 o 0 (booleano para activar/desactivar el descuento)
        
        Retorna: {"success": True/False, ...}
        """
        try:
            if descuento_pct < 0 or descuento_pct > 100:
                return {"success": False, "error": "El descuento debe estar entre 0 y 100%"}
            
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE productos
                SET descuento_pct = ?, descuento_activo = ?
                WHERE id = ?
                """,
                (descuento_pct, descuento_activo, producto_id)
            )

            if cursor.rowcount == 0:
                conn.close()
                return {"success": False, "error": "Producto no encontrado"}

            conn.commit()
            conn.close()
            return {"success": True, "data": None}

        except Exception as e:
            return {"success": False, "error": str(e)}
