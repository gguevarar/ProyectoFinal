"""
modelo_dicom.py
Modelo MVC — Procesamiento de Imágenes Médicas (DICOM / NIfTI)
Proyecto Final Informática II — Bioingeniería
"""

import os
import numpy as np
import pandas as pd
import cv2
import pydicom
import nibabel as nib
from datetime import datetime, timedelta


class ModeloDicom:
    """
    Encapsula toda la lógica de carga, preprocesamiento y análisis
    de archivos DICOM. Sigue el principio de separación de responsabilidades:
    esta clase NO sabe nada de PyQt ni de la interfaz.
    """

    def __init__(self):
        self.volumen_3d = None          # Matriz numpy con el volumen completo
        self.metadatos = {}             # Diccionario con info del paciente/estudio
        self.archivos_dicom = []        # Lista de datasets cargados
        self.es_tomografia = False      # Flag para saber si es CT y aplicar HU
        self.recorte_actual = None      # Última ROI extraída con OpenCV

    # ---------------------------------------------------------------
    # 1. CARGA DEL VOLUMEN DICOM
    # ---------------------------------------------------------------
    def cargar_serie_dicom(self, carpeta):
        """
        Lee todos los archivos .dcm de una carpeta, los ordena por
        posición de corte y arma el volumen 3D como atributo de clase.
        Retorna True si tuvo éxito, False si hubo error.
        """
        archivos = [
            os.path.join(carpeta, f)
            for f in os.listdir(carpeta)
            if f.lower().endswith(".dcm")
        ]

        if not archivos:
            return False, "No se encontraron archivos .dcm en la carpeta."

        # Cargamos cada slice y los ordenamos por ImagePositionPatient
        datasets = [pydicom.dcmread(a) for a in archivos]
        datasets.sort(key=lambda d: float(d.ImagePositionPatient[2]) if hasattr(d, "ImagePositionPatient") else 0)

        self.archivos_dicom = datasets

        # Apilamos los píxeles en un volumen 3D: (num_cortes, filas, columnas)
        slices = [d.pixel_array for d in datasets]
        self.volumen_3d = np.stack(slices, axis=0).astype(np.float64)

        # ¿Es CT? Lo detectamos por la modalidad del estudio
        modalidad = str(datasets[0].get("Modality", "")).upper()
        self.es_tomografia = (modalidad == "CT")

        if self.es_tomografia:
            self._convertir_a_hounsfield()

        self._extraer_metadatos(datasets[0])
        return True, "Serie cargada correctamente."

    # ---------------------------------------------------------------
    # 2. CONVERSIÓN A UNIDADES HOUNSFIELD (solo CT)
    # ---------------------------------------------------------------
    def _convertir_a_hounsfield(self):
        """
        Aplica la transformación lineal estándar:
            HU = pixel_value * RescaleSlope + RescaleIntercept
        usando los atributos DICOM del primer corte.
        """
        ds = self.archivos_dicom[0]
        slope = float(ds.get("RescaleSlope", 1))
        intercept = float(ds.get("RescaleIntercept", 0))
        self.volumen_3d = self.volumen_3d * slope + intercept

    # ---------------------------------------------------------------
    # 3. EXTRACCIÓN DE METADATOS
    # ---------------------------------------------------------------
    def _extraer_metadatos(self, ds):
        """
        Parsea los tags DICOM más relevantes y calcula la duración del estudio.
        Almacena todo en self.metadatos (diccionario).
        """
        fecha = str(ds.get("StudyDate", ""))
        hora_inicio = str(ds.get("StudyTime", ""))
        hora_serie = str(ds.get("SeriesTime", ""))

        # Calcular duración entre StudyTime y SeriesTime
        duracion = self._calcular_duracion(hora_inicio, hora_serie)

        self.metadatos = {
            "Paciente":           str(ds.get("PatientName", "Desconocido")),
            "ID Paciente":        str(ds.get("PatientID", "N/A")),
            "Fecha del Estudio":  self._formatear_fecha(fecha),
            "Hora del Estudio":   self._formatear_hora(hora_inicio),
            "Hora de la Serie":   self._formatear_hora(hora_serie),
            "Duración Estimada":  duracion,
            "Modalidad":          str(ds.get("Modality", "N/A")),
            "Fabricante":         str(ds.get("Manufacturer", "N/A")),
            "Institución":        str(ds.get("InstitutionName", "N/A")),
            "Descripción":        str(ds.get("StudyDescription", "N/A")),
            "Filas":              str(ds.get("Rows", "N/A")),
            "Columnas":           str(ds.get("Columns", "N/A")),
            "N° de Cortes":       str(len(self.archivos_dicom)),
        }

    def _formatear_fecha(self, fecha_dicom):
        try:
            return datetime.strptime(fecha_dicom, "%Y%m%d").strftime("%d/%m/%Y")
        except:
            return fecha_dicom

    def _formatear_hora(self, hora_dicom):
        try:
            return datetime.strptime(hora_dicom[:6], "%H%M%S").strftime("%H:%M:%S")
        except:
            return hora_dicom

    def _calcular_duracion(self, hora_ini, hora_fin):
        """Calcula diferencia de tiempo entre dos strings HHMMSS del DICOM."""
        try:
            t1 = datetime.strptime(hora_ini[:6], "%H%M%S")
            t2 = datetime.strptime(hora_fin[:6], "%H%M%S")
            delta = t2 - t1
            minutos = int(delta.total_seconds() / 60)
            return f"{minutos} min {int(delta.total_seconds() % 60)} s"
        except:
            return "No calculable"

    def guardar_metadatos_csv(self, ruta_csv="metadatos_estudio.csv"):
        """Exporta el diccionario de metadatos a un archivo CSV con Pandas."""
        df = pd.DataFrame(list(self.metadatos.items()), columns=["Campo", "Valor"])
        df.to_csv(ruta_csv, index=False, encoding="utf-8-sig")
        return ruta_csv

    def obtener_metadatos_como_lista(self):
        """
        Retorna lista de tuplas (campo, valor) para poblar un QTableWidget
        desde el controlador. El modelo no toca la interfaz.
        """
        return list(self.metadatos.items())

    # ---------------------------------------------------------------
    # 4. CONVERSIÓN A NIFTI
    # ---------------------------------------------------------------
    def convertir_a_nifti(self, ruta_salida="volumen_convertido.nii.gz"):
        """
        Toma el volumen 3D ya cargado y lo guarda como archivo NIfTI.
        El pixel spacing y slice thickness se usan para la matriz afín.
        """
        if self.volumen_3d is None:
            return False, "Primero debe cargar una serie DICOM."

        ds = self.archivos_dicom[0]

        # Obtenemos resolución espacial para la matriz afín
        try:
            ps = ds.PixelSpacing          # [row_spacing, col_spacing] en mm
            st = float(ds.SliceThickness) # grosor del corte en mm
        except AttributeError:
            ps = [1.0, 1.0]
            st = 1.0

        # Matriz afín identidad escalada por el spacing real
        afin = np.diag([float(ps[1]), float(ps[0]), st, 1.0])

        imagen_nifti = nib.Nifti1Image(self.volumen_3d, affine=afin)
        nib.save(imagen_nifti, ruta_salida)
        return True, f"NIfTI guardado en: {ruta_salida}"

    # ---------------------------------------------------------------
    # 5. OBTENER CORTES PARA EL VISUALIZADOR MULTIPLANAR
    # ---------------------------------------------------------------
    def obtener_corte(self, plano, indice):
        """
        Retorna un corte 2D normalizado a uint8 para mostrarlo en matplotlib.
        plano: 'axial' | 'sagital' | 'coronal'
        indice: número de corte dentro del rango del eje correspondiente
        """
        if self.volumen_3d is None:
            return None

        if plano == "axial":
            corte = self.volumen_3d[indice, :, :]
        elif plano == "sagital":
            corte = self.volumen_3d[:, :, indice]
        elif plano == "coronal":
            corte = self.volumen_3d[:, indice, :]
        else:
            return None

        return self._normalizar_a_uint8(corte)

    def obtener_dimensiones_volumen(self):
        """Retorna (axial, coronal, sagital) como máximos de índice para los sliders."""
        if self.volumen_3d is None:
            return (0, 0, 0)
        z, y, x = self.volumen_3d.shape
        return (z - 1, y - 1, x - 1)

    # ---------------------------------------------------------------
    # 6. HERRAMIENTA DE ZOOM Y RECORTE (OpenCV)
    # ---------------------------------------------------------------
    def _normalizar_a_uint8(self, imagen_2d):
        """
        Normalización estándar: (I - min) / (max - min) * 255
        Retorna array uint8.
        """
        minimo = imagen_2d.min()
        maximo = imagen_2d.max()
        if maximo == minimo:
            return np.zeros_like(imagen_2d, dtype=np.uint8)
        norm = (imagen_2d - minimo) / (maximo - minimo) * 255.0
        return norm.astype(np.uint8)

    def aplicar_zoom_y_recorte(self, plano, indice_corte, x1, y1, x2, y2, escala=2.0):
        """
        Toma un corte del volumen 3D, pasa a BGR (escala de grises en 3 canales),
        recorta la ROI definida por las coordenadas (x1,y1)-(x2,y2),
        redimensiona según 'escala', y dibuja el rectángulo sobre la imagen original.

        Retorna: (imagen_original_bgr, imagen_recortada_bgr, texto_dimensiones)
        """
        if self.volumen_3d is None:
            return None, None, ""

        corte_uint8 = self.obtener_corte(plano, indice_corte)

        # Convertir a BGR para poder usar funciones de color de OpenCV
        imagen_bgr = cv2.cvtColor(corte_uint8, cv2.COLOR_GRAY2BGR)

        # Recortar la región de interés
        roi = imagen_bgr[y1:y2, x1:x2]
        if roi.size == 0:
            return imagen_bgr, imagen_bgr, "ROI inválida"

        # Redimensionar (zoom)
        nuevo_ancho = int(roi.shape[1] * escala)
        nuevo_alto = int(roi.shape[0] * escala)
        roi_ampliada = cv2.resize(roi, (nuevo_ancho, nuevo_alto), interpolation=cv2.INTER_LINEAR)

        # Calcular dimensiones reales en mm usando el spacing del DICOM
        texto_dims = self._calcular_dimensiones_reales_mm(plano, x1, y1, x2, y2)

        # Dibujar el rectángulo rojo sobre la imagen original y el texto
        imagen_marcada = imagen_bgr.copy()
        cv2.rectangle(imagen_marcada, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(imagen_marcada, texto_dims, (x1, max(y1 - 8, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

        self.recorte_actual = roi_ampliada
        return imagen_marcada, roi_ampliada, texto_dims

    def _calcular_dimensiones_reales_mm(self, plano, x1, y1, x2, y2):
        """Usa PixelSpacing y SliceThickness para calcular el tamaño de la ROI en mm."""
        try:
            ds = self.archivos_dicom[0]
            ps = ds.PixelSpacing       # [row_spacing, col_spacing]
            st = float(ds.SliceThickness)
            ancho_mm = (x2 - x1) * float(ps[1])
            alto_mm  = (y2 - y1) * float(ps[0])
            return f"{ancho_mm:.1f} x {alto_mm:.1f} mm"
        except:
            return f"{x2 - x1} x {y2 - y1} px"

    def guardar_recorte(self, nombre_archivo):
        """Guarda el último recorte en disco con el nombre proporcionado."""
        if self.recorte_actual is None:
            return False, "No hay recorte disponible para guardar."
        os.makedirs("recortes", exist_ok=True)
        ruta = os.path.join("recortes", nombre_archivo)
        cv2.imwrite(ruta, self.recorte_actual)
        return True, f"Recorte guardado en: {ruta}"

    # ---------------------------------------------------------------
    # 7. SEGMENTACIÓN Y MORFOLOGÍA
    # ---------------------------------------------------------------
    def aplicar_binarizacion(self, imagen_gray, umbral, tipo_cv2):
        """
        Aplica umbralización de OpenCV sobre una imagen en escala de grises.
        tipo_cv2: cv2.THRESH_BINARY, cv2.THRESH_BINARY_INV, etc.
        Retorna la imagen binarizada.
        """
        _, binarizada = cv2.threshold(imagen_gray, umbral, 255, tipo_cv2)
        return binarizada

    def aplicar_morfologia(self, imagen_binaria, operacion_cv2, tam_kernel):
        """
        Aplica una operación morfológica sobre la imagen binaria.
        operacion_cv2: cv2.MORPH_OPEN, cv2.MORPH_CLOSE, cv2.MORPH_ERODE, etc.
        tam_kernel: entero impar (3, 5, 7...)
        """
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (tam_kernel, tam_kernel)
        )
        resultado = cv2.morphologyEx(imagen_binaria, operacion_cv2, kernel)
        return resultado
