import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QGridLayout, QGroupBox, QSizePolicy, QHeaderView, QFrame,
    QScrollArea, QComboBox, QSpacerItem)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
from database import DatabaseManager

class AlgoBonitoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = True
        self.setStyleSheet(self._get_dark_theme() if self.dark_mode else self._get_light_theme())
        
        self.db_manager = DatabaseManager()
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.initUI()
        self.load_products()
        self.update_statistics()

    def _clean_monetary_value(self, value):
        """Limpia un valor monetario quitando el símbolo $ y las comas"""
        if isinstance(value, (int, float)):
            return float(value)
        try:
            # Quitar el símbolo $ y las comas, luego convertir a float
            cleaned = value.replace('$', '').replace(',', '').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            raise ValueError(f"Valor monetario inválido: {value}")

    def add_product(self):
        try:
            product_id = self.product_id_input.text()
            name = self.name_input.text()
            unit_price_text = self.unit_price_input.text()
            status = self.status_input.text()
            brand = self.brand_input.text()
            color = self.color_input.text()
            model = self.model_input.text()
            quantity_text = self.quantity_input.text()
            price_total_text = self.price_total_input.text()

            # Validaciones de campos de texto vacíos
            if not product_id:
                QMessageBox.warning(self, "Advertencia", "El campo 'ID del Producto' no puede estar vacío.")
                return
            if not name:
                QMessageBox.warning(self, "Advertencia", "El campo 'Nombre del Producto' no puede estar vacío.")
                return
            if not status:
                QMessageBox.warning(self, "Advertencia", "El campo 'Estado del Producto' no puede estar vacío.")
                return
            if not brand:
                QMessageBox.warning(self, "Advertencia", "El campo 'Marca' no puede estar vacío.")
                return
            if not color:
                QMessageBox.warning(self, "Advertencia", "El campo 'Color' no puede estar vacío.")
                return
            if not model:
                QMessageBox.warning(self, "Advertencia", "El campo 'Modelo' no puede estar vacío.")
                return

            # Validaciones de campos numéricos
            try:
                unit_price = self._clean_monetary_value(unit_price_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Precio Unitario' sea un número válido (ejemplo: $25.00).")
                return

            try:
                quantity = int(quantity_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Cantidad' sea un número entero válido.")
                return

            try:
                price_total = self._clean_monetary_value(price_total_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Precio Total' sea un número válido (ejemplo: $100.00).")
                return

            product_data = (product_id, name, unit_price, status, brand, color, model, quantity, price_total)
            self.db_manager.add_product(product_data)
            QMessageBox.information(self, "Éxito", "Producto añadido correctamente.")
            self.clear_inputs()
            self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al añadir producto: {e}")
            
    # ... resto del código existente ...
