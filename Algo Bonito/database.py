import pypyodbc
import os
import traceback
import sys
import platform

class DatabaseManager:
    @staticmethod
    def clean_monetary_value(value):
        """Limpia un valor monetario, removiendo símbolos de moneda y convirtiendo a float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remover símbolos de moneda y espacios
            cleaned = value.replace('$', '').replace('€', '').replace('£', '').strip()
            # Remover comas si existen
            cleaned = cleaned.replace(',', '')
            try:
                return float(cleaned)
            except ValueError:
                print(f"ERROR: No se pudo convertir el valor monetario: {value}")
                return 0.0
        return 0.0

    @staticmethod
    def check_access_driver():
        try:
            print("\n=== Diagnóstico del Sistema ===")
            print(f"Python Version: {sys.version}")
            print(f"Python Architecture: {'64 bit' if sys.maxsize > 2**32 else '32 bit'}")
            print(f"OS Architecture: {platform.architecture()[0]}")
            print(f"Platform: {platform.platform()}")
            
            # Lista todos los drivers disponibles
            drivers = [x for x in pypyodbc.drivers() if x.startswith('Microsoft Access Driver')]
            if drivers:
                print("\nDrivers de Access encontrados:")
                for driver in drivers:
                    print(f"  - {driver}")
                # Intentar determinar la arquitectura del driver
                try:
                    import winreg
                    for driver in drivers:
                        try:
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\ODBC\ODBCINST.INI\\' + driver) as key:
                                path = winreg.QueryValue(key, 'Driver')
                                print(f"  Path del driver: {path}")
                                if '64' in path:
                                    print("  (Parece ser un driver de 64 bits)")
                                elif '32' in path or 'x86' in path:
                                    print("  (Parece ser un driver de 32 bits)")
                        except Exception as e:
                            print(f"  No se pudo determinar la arquitectura del driver: {e}")
                except Exception as e:
                    print(f"Error al acceder al registro de Windows: {e}")
                return True
            else:
                print("\nERROR: No se encontró el Driver de Microsoft Access.")
                print("Drivers ODBC disponibles:")
                all_drivers = pypyodbc.drivers()
                for driver in all_drivers:
                    print(f"  - {driver}")
                return False
        except Exception as e:
            print(f"\nError al verificar drivers: {e}")
            return False

    def __init__(self):
        self.conn = None
        self.table_name = "Inventario"  # Nombre de la tabla por defecto
        self.conn_str = ""  # Inicializar como cadena vacía para Pylance
        try:
            # Obtener la ruta de AppData
            appdata_path = os.path.join(os.getenv('APPDATA') or '', 'AlgoBonito')
            os.makedirs(appdata_path, exist_ok=True)
            
            # Ruta de la base de datos
            db_path = os.path.join(appdata_path, 'Database2.accdb')
            
            # Si el archivo no existe en AppData, copiarlo desde el directorio actual
            if not os.path.exists(db_path):
                current_db = 'Database2.accdb'
                if os.path.exists(current_db):
                    import shutil
                    shutil.copy2(current_db, db_path)
                    print(f"Base de datos copiada a: {db_path}")
            
            # Intentar primero con el driver de 64 bits
            drivers = [
                'Microsoft Access Driver (*.mdb, *.accdb)',
                'Microsoft Access Driver (*.mdb)',
                'Driver do Microsoft Access (*.mdb)',
                'Microsoft Access Driver (*.mdb, *.accdb)',
                'Microsoft.ACE.OLEDB.12.0'
            ]
            
            connection_error = None
            for driver in drivers:
                try:
                    temp_conn_str = f'Driver={{{driver}}};DBQ={db_path};'
                    print(f"\nIntentando conectar con driver: {driver}")
                    self.conn = pypyodbc.connect(temp_conn_str)
                    self.conn_str = temp_conn_str # Asignar solo si la conexión es exitosa
                    print("¡Conexión exitosa!")
                    self._create_table_if_not_exists() # Asegurarse de que la tabla se cree
                    connection_error = None
                    break
                except Exception as e:
                    connection_error = str(e)
                    print(f"Error con driver {driver}: {e}")
                    continue
            
            if connection_error is not None:
                print("\n=== ERROR DE CONEXIÓN ===")
                print("No se pudo conectar con ningún driver de Microsoft Access.")
                print("\nSolución sugerida:")
                print("1. Descargue e instale el driver ODBC de Access de 32 bits desde:")
                print("   https://www.microsoft.com/en-us/download/details.aspx?id=13255")
                print("2. Si ya tiene Office de 64 bits, instale el driver de 64 bits:")
                print("   https://www.microsoft.com/en-us/download/details.aspx?id=54920")
                print("3. Reinicie su equipo tras la instalación si es necesario.")
                print("\nInformación de diagnóstico:")
                self.check_access_driver()
                print(f"\nÚltimo error: {connection_error}")
                raise Exception("No se pudo establecer conexión con la base de datos.\nPor favor, instale el driver ODBC de Access adecuado para su sistema.")
                
        except Exception as e:
            print(f"\nError crítico al inicializar la base de datos:")
            print(str(e))
            print("\nStack trace completo:")
            traceback.print_exc()
            raise

    def _get_connection(self):
        try:
            print("DEBUG: Intentando establecer conexión...")
            conn = pypyodbc.connect(self.conn_str)
            print("DEBUG: Conexión establecida exitosamente")
            return conn
        except Exception as e:
            print(f"ERROR: No se pudo establecer la conexión: {str(e)}")
            print(f"Detalles: {traceback.format_exc()}")
            print("--- Diagnóstico de drivers ODBC disponibles ---")
            try:
                drivers = pypyodbc.drivers()
                print("Drivers ODBC detectados:")
                for d in drivers:
                    print(f"  - {d}")
            except Exception as ed:
                print(f"Error al listar drivers ODBC: {ed}")
            print(f"Cadena de conexión usada: {self.conn_str}")
            raise

    def _create_table_if_not_exists(self):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE [{self.table_name}] (
                    [ID del producto] TEXT PRIMARY KEY,
                    [Nombre del producto] TEXT,
                    [Precio unitario] DOUBLE,
                    [Estado del producto] TEXT,
                    [Marca] TEXT,
                    [Color] TEXT,
                    [Modelo] TEXT,
                    [Cantidad de producto] INTEGER,
                    [Precio] DOUBLE
                )
            """)
            conn.commit()
            print(f"DEBUG: Tabla '{self.table_name}' verificada/creada exitosamente.")
        except pypyodbc.Error as ex:
            sqlstate = ex.args[0]
            if sqlstate == '42S01': # Table already exists
                print(f"DEBUG: La tabla '{self.table_name}' ya existe (SQLSTATE: {sqlstate}).")
            else:
                print(f"ERROR: Error al crear/verificar la tabla '{self.table_name}': {ex}")
                print(f"SQLSTATE: {sqlstate}")
                print(f"Detalles: {traceback.format_exc()}")
                raise
        finally:
            if conn:
                conn.close()

    def get_all_products(self):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM [{self.table_name}]")
            return cursor.fetchall()
        except pypyodbc.Error as ex:
            print(f"Error al obtener productos: {ex}")
            print(f"Detalles: {traceback.format_exc()}")
            return []
        finally:
            if conn:
                conn.close()

    def add_product(self, product_data):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Limpiar valores monetarios
            cleaned_data = list(product_data)
            # El índice 2 es Precio unitario y el índice 8 es Precio
            cleaned_data[2] = self.clean_monetary_value(product_data[2])
            cleaned_data[8] = self.clean_monetary_value(product_data[8])
            
            print(f"DEBUG: Valores monetarios limpios - Precio unitario: {cleaned_data[2]}, Precio: {cleaned_data[8]}")
            
            cursor.execute(f"""
                INSERT INTO [{self.table_name}] (
                    [ID del producto], [Nombre del producto], [Precio unitario],
                    [Estado del producto], [Marca], [Color], [Modelo],
                    [Cantidad de producto], [Precio]
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, cleaned_data)
            conn.commit()
        except pypyodbc.Error as ex:
            print(f"Error al añadir producto: {ex}")
            print(f"Detalles: {traceback.format_exc()}")
            raise Exception(f"Error de base de datos al añadir producto: {ex}")
        finally:
            if conn:
                conn.close()

    def update_product(self, product_id, product_data):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Limpiar valores monetarios
            cleaned_data = list(product_data)
            # El índice 1 es Precio unitario y el índice 7 es Precio en la actualización
            cleaned_data[1] = self.clean_monetary_value(product_data[1])
            cleaned_data[7] = self.clean_monetary_value(product_data[7])
            
            print(f"DEBUG: Valores monetarios limpios - Precio unitario: {cleaned_data[1]}, Precio: {cleaned_data[7]}")
            
            cursor.execute(f"""
                UPDATE [{self.table_name}] SET
                    [Nombre del producto] = ?,
                    [Precio unitario] = ?,
                    [Estado del producto] = ?,
                    [Marca] = ?,
                    [Color] = ?,
                    [Modelo] = ?,
                    [Cantidad de producto] = ?,
                    [Precio] = ?
                WHERE [ID del producto] = ?
            """, (*cleaned_data, product_id))
            conn.commit()
        except pypyodbc.Error as ex:
            print(f"Error al actualizar producto: {ex}")
            print(f"Detalles: {traceback.format_exc()}")
            raise Exception(f"Error de base de datos al actualizar producto: {ex}")
        finally:
            if conn:
                conn.close()

    def delete_product(self, product_id):
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM [{self.table_name}] WHERE [ID del producto] = ?", [product_id])
            conn.commit()
        except pypyodbc.Error as ex:
            print(f"Error al eliminar producto: {ex}")
            print(f"Detalles: {traceback.format_exc()}")
            raise Exception(f"Error de base de datos al eliminar producto: {ex}")
        finally:
            if conn:
                conn.close()
