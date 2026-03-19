from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLabel
)
from PySide6.QtCore import Qt

# Lógica Dev2 (tu CRUD)
from modules.inventory import InventoryManager


class InventoryPage(QWidget):

    def __init__(self):
        super().__init__()

        self.inv = InventoryManager()
        self.producto_seleccionado = None

        self._build_ui()
        self.cargar_productos()

    # ---------------- UI ---------------- #

    def _build_ui(self):
        layout = QVBoxLayout(self)

        titulo = QLabel("Gestión de Inventario")
        titulo.setStyleSheet("font-size: 20px; font-weight: bold;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # -------- Formulario -------- #
        form_layout = QFormLayout()

        self.input_nombre = QLineEdit()
        self.input_precio = QLineEdit()
        self.input_cantidad = QLineEdit()
        self.input_categoria = QLineEdit()

        form_layout.addRow("Nombre:", self.input_nombre)
        form_layout.addRow("Precio:", self.input_precio)
        form_layout.addRow("Cantidad:", self.input_cantidad)
        form_layout.addRow("Categoría:", self.input_categoria)

        layout.addLayout(form_layout)

        # -------- Botones -------- #
        btn_layout = QHBoxLayout()

        btn_agregar = QPushButton("Agregar")
        btn_actualizar = QPushButton("Actualizar")
        btn_eliminar = QPushButton("Eliminar")
        btn_refrescar = QPushButton("Refrescar")

        btn_agregar.clicked.connect(self.agregar_producto)
        btn_actualizar.clicked.connect(self.actualizar_producto)
        btn_eliminar.clicked.connect(self.eliminar_producto)
        btn_refrescar.clicked.connect(self.cargar_productos)

        btn_layout.addWidget(btn_agregar)
        btn_layout.addWidget(btn_actualizar)
        btn_layout.addWidget(btn_eliminar)
        btn_layout.addWidget(btn_refrescar)

        layout.addLayout(btn_layout)

        # -------- Tabla -------- #
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Precio", "Cantidad", "Categoría"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.cellClicked.connect(self.seleccionar_producto)

        layout.addWidget(self.tabla)

    # ---------------- Funciones ---------------- #

    def cargar_productos(self):
        resultado = self.inv.get_all()

        if not resultado["success"]:
            return

        data = resultado["data"]
        self.tabla.setRowCount(len(data))

        for row, p in enumerate(data):
            self.tabla.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self.tabla.setItem(row, 1, QTableWidgetItem(p["nombre"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(str(p["precio"])))
            self.tabla.setItem(row, 3, QTableWidgetItem(str(p["cantidad"])))
            self.tabla.setItem(row, 4, QTableWidgetItem(p["categoria"] or ""))

        self.tabla.resizeColumnsToContents()

    def limpiar_formulario(self):
        self.input_nombre.clear()
        self.input_precio.clear()
        self.input_cantidad.clear()
        self.input_categoria.clear()
        self.producto_seleccionado = None

    def _datos_validos(self):
        if self.input_nombre.text().strip() == "":
            QMessageBox.warning(self, "Aviso", "El nombre es obligatorio")
            return False

        if not self.input_precio.text().replace(".", "", 1).isdigit():
            QMessageBox.warning(self, "Aviso", "Precio inválido")
            return False

        if not self.input_cantidad.text().isdigit():
            QMessageBox.warning(self, "Aviso", "Cantidad inválida")
            return False

        return True

    def agregar_producto(self):
        if not self._datos_validos():
            return

        self.inv.add(
            self.input_nombre.text(),
            float(self.input_precio.text()),
            int(self.input_cantidad.text()),
            self.input_categoria.text()
        )

        self.cargar_productos()
        self.limpiar_formulario()

    def seleccionar_producto(self, row, column):
        self.producto_seleccionado = int(self.tabla.item(row, 0).text())

        self.input_nombre.setText(self.tabla.item(row, 1).text())
        self.input_precio.setText(self.tabla.item(row, 2).text())
        self.input_cantidad.setText(self.tabla.item(row, 3).text())
        self.input_categoria.setText(self.tabla.item(row, 4).text())

    def actualizar_producto(self):
        if not self.producto_seleccionado:
            QMessageBox.warning(self, "Aviso", "Seleccione un producto")
            return

        if not self._datos_validos():
            return

        self.inv.update(
            self.producto_seleccionado,
            self.input_nombre.text(),
            float(self.input_precio.text()),
            int(self.input_cantidad.text()),
            self.input_categoria.text()
        )

        self.cargar_productos()
        self.limpiar_formulario()

    def eliminar_producto(self):
        if not self.producto_seleccionado:
            QMessageBox.warning(self, "Aviso", "Seleccione un producto")
            return

        self.inv.delete(self.producto_seleccionado)
        self.cargar_productos()
        self.limpiar_formulario()