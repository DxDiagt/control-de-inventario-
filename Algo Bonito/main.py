import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QMessageBox, QGridLayout, QGroupBox, QSizePolicy, QHeaderView, QFrame,
    QScrollArea, QComboBox, QSpacerItem)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor, QPalette
from database import DatabaseManager
import shutil
import os

class AlgoBonitoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Configurar el tema oscuro
        self.dark_mode = True
        self.setStyleSheet(self._get_dark_theme() if self.dark_mode else self._get_light_theme())
        
        # Definir ruta AppData
        appdata_dir = os.path.join(os.environ['APPDATA'], 'AlgoBonito')
        if not os.path.exists(appdata_dir):
            os.makedirs(appdata_dir)
        db_dest = os.path.join(appdata_dir, 'Database2.accdb')
        # Copiar la base de datos si no existe en AppData
        if not os.path.exists(db_dest):
            try:
                shutil.copyfile(os.path.join(os.path.dirname(sys.argv[0]), 'Database2.accdb'), db_dest)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo copiar la base de datos a AppData: {e}\nLa aplicación se cerrará.")
                sys.exit(1) # Salir de la aplicación de forma controlada
        self.db_manager = DatabaseManager()
        
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        self.initUI()
        self.load_products()
        self.update_statistics()

    def initUI(self):
        self.setWindowTitle('Algo Bonito - Gestión de Inventario')
        self.setGeometry(100, 100, 1280, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header con título y botón de tema
        header_layout = QHBoxLayout()
        title = QLabel("Algo Bonito - Gestión de Inventario")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            padding: 10px;
            border-radius: 10px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1976D2, stop:1 #64B5F6);
            color: white;
        """)
        header_layout.addWidget(title)
        
        theme_button = QPushButton("🌓 Cambiar Tema")
        theme_button.setFixedWidth(150)
        theme_button.clicked.connect(self.toggle_theme)
        header_layout.addWidget(theme_button)
        
        main_layout.addLayout(header_layout)

        # Panel de estadísticas
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout()
        self.total_products_label = QLabel("Total Productos: 0")
        self.total_value_label = QLabel("Valor Total: $0.00")
        self.low_stock_label = QLabel("Stock Bajo: 0")
        for label in [self.total_products_label, self.total_value_label, self.low_stock_label]:
            stats_layout.addWidget(label)
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)

        # Barra de búsqueda
        search_group = QGroupBox("Búsqueda")
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por ID, nombre, marca...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(self.search_input)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Stock Bajo", "Activos", "Inactivos"])
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        search_layout.addWidget(self.filter_combo)
        
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        # Formulario de entrada en un área scrolleable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll.setWidget(scroll_content)
        form_layout = QGridLayout(scroll_content)

        # Campos del formulario
        input_fields = [
            ("ID del Producto:", "product_id_input"),
            ("Nombre del Producto:", "name_input"),
            ("Precio Unitario:", "unit_price_input"),
            ("Estado del Producto:", "status_input"),
            ("Marca:", "brand_input"),
            ("Color:", "color_input"),
            ("Modelo:", "model_input"),
            ("Cantidad:", "quantity_input"),
            ("Precio Total:", "price_total_input")
        ]

        for row, (label_text, input_name) in enumerate(input_fields):
            label = QLabel(label_text)
            line_edit = QLineEdit()
            line_edit.setObjectName(input_name)
            setattr(self, input_name, line_edit)
            
            form_layout.addWidget(label, row, 0)
            form_layout.addWidget(line_edit, row, 1)
            
            if row % 2 == 0 and row < len(input_fields) - 1:
                label2 = QLabel(input_fields[row + 1][0])
                line_edit2 = QLineEdit()
                line_edit2.setObjectName(input_fields[row + 1][1])
                setattr(self, input_fields[row + 1][1], line_edit2)
                
                form_layout.addWidget(label2, row, 2)
                form_layout.addWidget(line_edit2, row, 3)

        main_layout.addWidget(scroll)

        # Botones de acción
        button_layout = QHBoxLayout()
        buttons = [
            ("➕ Añadir", self.add_product),
            ("🔄 Actualizar", self.update_product),
            ("❌ Eliminar", self.delete_product),
            ("🧹 Limpiar", self.clear_inputs)
        ]
        
        for text, slot in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            button_layout.addWidget(btn)

        main_layout.addLayout(button_layout)

        # Tabla de productos
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(9)
        self.table_widget.setHorizontalHeaderLabels([
            "ID", "Nombre", "Precio Unit.", "Estado",
            "Marca", "Color", "Modelo", "Cantidad", "Precio Total"
        ])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.itemSelectionChanged.connect(self.display_selected_product)
        main_layout.addWidget(self.table_widget)

        # Footer
        footer = QLabel("© 2025 Algo Bonito - Gestión de Inventario | Desarrollado por B")
        try:
            footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        except AttributeError:
            footer.setAlignment(Qt.AlignCenter) # type: ignore
        main_layout.addWidget(footer)

    def _create_input_field(self, label_text): # Ya no recibe layout, row, col
        label = QLabel(label_text)
        line_edit = QLineEdit()
        line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Expandir horizontalmente, fijo verticalmente
        return label, line_edit # Devolver la etiqueta y el campo de entrada

    def load_products(self):
        products = self.db_manager.get_all_products()
        self.table_widget.setRowCount(len(products))
        for row_idx, product in enumerate(products):
            for col_idx, value in enumerate(product):
                item = QTableWidgetItem(str(value))
                if col_idx in [2, 8]:  # Formato para precios
                    try:
                        num_value = float(value)
                        item.setText(f"${num_value:,.2f}")
                    except (ValueError, TypeError):
                        item.setText(str(value))
                else:
                    item.setText(str(value))
                self.table_widget.setItem(row_idx, col_idx, item)
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
                unit_price = float(unit_price_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Precio Unitario' sea un número válido.")
                return

            try:
                quantity = int(quantity_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Cantidad' sea un número entero válido.")
                return

            try:
                price_total = float(price_total_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Precio Total' sea un número válido.")
                return

            product_data = (product_id, name, unit_price, status, brand, color, model, quantity, price_total)
            self.db_manager.add_product(product_data)
            QMessageBox.information(self, "Éxito", "Producto añadido correctamente.")
            self.clear_inputs()
            self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al añadir producto: {e}")

    def update_product(self):
        try:
            selected_row = self.table_widget.currentRow()
            if selected_row == -1:
                QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un producto para actualizar.")
                return

            product_id = self.table_widget.item(selected_row, 0).text()
            
            name = self.name_input.text()
            unit_price_text = self.unit_price_input.text()
            status = self.status_input.text()
            brand = self.brand_input.text()
            color = self.color_input.text()
            model = self.model_input.text()
            quantity_text = self.quantity_input.text()
            price_total_text = self.price_total_input.text()

            # Validaciones de campos de texto vacíos
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
                unit_price = float(unit_price_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Precio Unitario' sea un número válido.")
                return

            try:
                quantity = int(quantity_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Cantidad' sea un número entero válido.")
                return

            try:
                price_total = float(price_total_text)
            except ValueError:
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Precio Total' sea un número válido.")
                return

            product_data = (name, unit_price, status, brand, color, model, quantity, price_total)
            self.db_manager.update_product(product_id, product_data)
            QMessageBox.information(self, "Éxito", "Producto actualizado correctamente.")
            self.clear_inputs()
            self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar producto: {e}")

    def delete_product(self):
        try:
            selected_row = self.table_widget.currentRow()
            if selected_row == -1:
                QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un producto para eliminar.")
                return

            product_id = self.table_widget.item(selected_row, 0).text()
            reply = QMessageBox.question(self, 'Confirmar Eliminación',
                                         f"¿Estás seguro de que quieres eliminar el producto con ID {product_id}?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.db_manager.delete_product(product_id)
                QMessageBox.information(self, "Éxito", "Producto eliminado correctamente.")
                self.clear_inputs()
                self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al eliminar producto: {e}")

    def display_selected_product(self):
        selected_items = self.table_widget.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            self.product_id_input.setText(self.table_widget.item(row, 0).text())
            self.name_input.setText(self.table_widget.item(row, 1).text())
            self.unit_price_input.setText(self.table_widget.item(row, 2).text())
            self.status_input.setText(self.table_widget.item(row, 3).text())
            self.brand_input.setText(self.table_widget.item(row, 4).text())
            self.color_input.setText(self.table_widget.item(row, 5).text())
            self.model_input.setText(self.table_widget.item(row, 6).text())
            self.quantity_input.setText(self.table_widget.item(row, 7).text())
            self.price_total_input.setText(self.table_widget.item(row, 8).text())
        else:
            self.clear_inputs()

    def _get_product_data_from_inputs(self, include_id=True):
        try:
            product_id = self.product_id_input.text() if include_id else None
            name = self.name_input.text()
            unit_price = float(self.unit_price_input.text())
            status = self.status_input.text()
            brand = self.brand_input.text()
            color = self.color_input.text()
            model = self.model_input.text()
            quantity = int(self.quantity_input.text())
            price_total = float(self.price_total_input.text())

            if not name:
                QMessageBox.warning(self, "Advertencia", "El campo 'Nombre del Producto' no puede estar vacío.")
                return None
            if not status:
                QMessageBox.warning(self, "Advertencia", "El campo 'Estado del Producto' no puede estar vacío.")
                return None
            if not brand:
                QMessageBox.warning(self, "Advertencia", "El campo 'Marca' no puede estar vacío.")
                return None
            if not color:
                QMessageBox.warning(self, "Advertencia", "El campo 'Color' no puede estar vacío.")
                return None
            if not model:
                QMessageBox.warning(self, "Advertencia", "El campo 'Modelo' no puede estar vacío.")
                return None

            if include_id and not product_id:
                QMessageBox.warning(self, "Advertencia", "Por favor, introduce un ID de producto.")
                return None

            return (product_id, name, unit_price, status, brand, color, model, quantity, price_total) if include_id else \
                   (name, unit_price, status, brand, color, model, quantity, price_total)
        except ValueError as ve:
            if "could not convert string to float" in str(ve):
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Precio Unitario' y 'Precio Total' sean números válidos.")
            elif "invalid literal for int" in str(ve):
                QMessageBox.warning(self, "Error de Entrada", "Asegúrate de que 'Cantidad' sea un número entero válido.")
            else:
                QMessageBox.warning(self, "Error de Entrada", f"Error de formato de datos: {ve}")
            return None

    def clear_inputs(self):
        self.product_id_input.clear()
        self.name_input.clear()
        self.unit_price_input.clear()
        self.status_input.clear()
        self.brand_input.clear()
        self.color_input.clear()
        self.model_input.clear()
        self.quantity_input.clear()
        self.price_total_input.clear()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.setStyleSheet(self._get_dark_theme() if self.dark_mode else self._get_light_theme())

    def on_search_changed(self):
        # Reinicia el temporizador cada vez que el texto cambia
        self.search_timer.stop()
        self.search_timer.start(300)  # Espera 300ms antes de realizar la búsqueda

    def perform_search(self):
        search_text = self.search_input.text().lower()
        for row in range(self.table_widget.rowCount()):
            hide_row = True
            if search_text:
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item and search_text in item.text().lower():
                        hide_row = False
                        break
            else:
                hide_row = False
            self.table_widget.setRowHidden(row, hide_row)

    def update_statistics(self):
        total_products = self.table_widget.rowCount()
        total_value = 0.0
        low_stock = 0
        for row in range(total_products):
            try:
                value = self.table_widget.item(row, 8)
                if value:
                    total_value += float(value.text().replace('$', '').replace(',', ''))
                stock = self.table_widget.item(row, 7)
                if stock and int(stock.text()) < 5:
                    low_stock += 1
            except Exception:
                continue
        self.total_products_label.setText(f"Total Productos: {total_products}")
        try:
            self.total_value_label.setText(f"Valor Total: ${float(total_value):,.2f}")
        except (ValueError, TypeError):
            self.total_value_label.setText(f"Valor Total: {total_value}")
        self.low_stock_label.setText(f"Stock Bajo: {low_stock}")

    def _get_dark_theme(self):
        return """
            QMainWindow {
                background-color: #1E1E1E;
            }
            QWidget {
                background-color: #2D2D2D;
                color: #FFFFFF;
                border-radius: 8px;
            }
            QGroupBox {
                background-color: #363636;
                border: 2px solid #4A4A4A;
                border-radius: 10px;
                margin-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                background-color: #0D47A1;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QLabel {
                color: #E0E0E0;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #424242;
                border: 2px solid #4A4A4A;
                border-radius: 6px;
                padding: 8px;
                color: #FFFFFF;
                selection-background-color: #0D47A1;
            }
            QLineEdit:focus {
                border: 2px solid #0D47A1;
            }
            QPushButton {
                background-color: #0D47A1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
            QPushButton:pressed {
                background-color: #0A3D8F;
            }
            QTableWidget {
                background-color: #2D2D2D;
                border: 2px solid #4A4A4A;
                gridline-color: #4A4A4A;
                color: #FFFFFF;
            }
            QTableWidget::item:selected {
                background-color: #0D47A1;
            }
            QHeaderView::section {
                background-color: #363636;
                color: #FFFFFF;
                padding: 6px;
                border: 1px solid #4A4A4A;
            }
            QScrollBar:vertical {
                background-color: #2D2D2D;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #4A4A4A;
                border-radius: 7px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #555555;
            }
            QMenu {
                background-color: #2D2D2D;
                border: 1px solid #4A4A4A;
            }
            QMenu::item {
                color: #FFFFFF;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #0D47A1;
            }
        """

    def _get_light_theme(self):
        return """
            QMainWindow {
                background-color: #F5F5F5;
            }
            QWidget {
                background-color: #FFFFFF;
                color: #222222;
                border-radius: 8px;
            }
            QGroupBox {
                background-color: #F0F0F0;
                border: 2px solid #CCCCCC;
                border-radius: 10px;
                margin-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                background-color: #1976D2;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #FAFAFA;
                border: 2px solid #CCCCCC;
                border-radius: 6px;
                padding: 8px;
                color: #222222;
                selection-background-color: #1976D2;
            }
            QLineEdit:focus {
                border: 2px solid #1976D2;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2196F3;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 2px solid #CCCCCC;
                gridline-color: #CCCCCC;
                color: #222222;
            }
            QTableWidget::item:selected {
                background-color: #1976D2;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                color: #222222;
                padding: 6px;
                border: 1px solid #CCCCCC;
            }
            QScrollBar:vertical {
                background-color: #FFFFFF;
                width: 14px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #CCCCCC;
                border-radius: 7px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #B0B0B0;
            }
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
            }
            QMenu::item {
                color: #222222;
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #1976D2;
            }
        """

    def apply_filter(self, text):
        # TODO: Implementar lógica de filtrado según el texto seleccionado
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AlgoBonitoApp()
    window.show()
    sys.exit(app.exec_())
