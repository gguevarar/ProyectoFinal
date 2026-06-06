"""
modelo_tablas.py
Modelo MVC — Procesamiento de Datos Tabulares Médicos
Proyecto Final Informática II — Bioingeniería
"""

import pandas as pd
import io


class ModeloTablas:
    """
    Gestiona la carga, descripción estadística y preparación de datos
    de archivos CSV o Excel de enfoque médico.
    """

    def __init__(self):
        self.df = None              # DataFrame principal cargado
        self.ruta_archivo = ""

    # ---------------------------------------------------------------
    # 1. CARGA DE ARCHIVO
    # ---------------------------------------------------------------
    def cargar_archivo(self, ruta):
        """
        Detecta la extensión y carga el archivo correctamente.
        Retorna (True, mensaje) o (False, mensaje_error).
        """
        try:
            ext = ruta.lower().split(".")[-1]
            if ext == "csv":
                # Intentamos con punto y coma primero (formato europeo/colombiano)
                try:
                    self.df = pd.read_csv(ruta, sep=";")
                    if self.df.shape[1] == 1:   # si quedó en una sola columna, usamos coma
                        self.df = pd.read_csv(ruta, sep=",")
                except:
                    self.df = pd.read_csv(ruta)
            elif ext in ("xlsx", "xls"):
                self.df = pd.read_excel(ruta)
            else:
                return False, f"Formato '{ext}' no soportado. Use .csv o .xlsx."

            self.ruta_archivo = ruta
            filas, cols = self.df.shape
            return True, f"Archivo cargado: {filas} filas × {cols} columnas."
        except Exception as e:
            return False, f"Error al leer el archivo: {str(e)}"

    # ---------------------------------------------------------------
    # 2. INFORMACIÓN PARA QTableWidget
    # ---------------------------------------------------------------
    def obtener_columnas_numericas(self):
        """Retorna lista de nombres de columnas con tipo numérico."""
        if self.df is None:
            return []
        return list(self.df.select_dtypes(include="number").columns)

    def obtener_todas_las_columnas(self):
        if self.df is None:
            return []
        return list(self.df.columns)

    def obtener_describe_como_lista(self):
        """
        Retorna el resultado de df.describe() en formato de lista de filas
        para poblar un QTableWidget: (encabezados, filas).
        """
        if self.df is None:
            return [], []

        desc = self.df.describe().reset_index()
        encabezados = list(desc.columns)
        filas = [list(row) for _, row in desc.iterrows()]
        return encabezados, filas

    def obtener_info_como_lista(self):
        """
        Captura df.info() como texto y lo convierte en lista de tuplas
        para mostrar en un QTableWidget de dos columnas (columna, dtype).
        """
        if self.df is None:
            return [], []

        encabezados = ["Columna", "Tipo", "No Nulos", "Nulos"]
        filas = []
        total = len(self.df)
        for col in self.df.columns:
            no_nulos = self.df[col].count()
            nulos    = total - no_nulos
            filas.append([col, str(self.df[col].dtype), str(no_nulos), str(nulos)])
        return encabezados, filas

    # ---------------------------------------------------------------
    # 3. PREPARACIÓN DE DATOS PARA GRÁFICAS
    # ---------------------------------------------------------------
    def obtener_serie(self, nombre_columna):
        """Retorna la serie de una columna para graficarla."""
        if self.df is None or nombre_columna not in self.df.columns:
            return None
        return self.df[nombre_columna].dropna()

    def obtener_dos_series_para_scatter(self, col_x, col_y):
        """
        Retorna dos series alineadas (sin NaN) para un gráfico de dispersión.
        """
        if self.df is None:
            return None, None
        datos = self.df[[col_x, col_y]].dropna()
        return datos[col_x], datos[col_y]
