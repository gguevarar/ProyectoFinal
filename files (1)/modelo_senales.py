"""
modelo_senales.py
Modelo MVC — Procesamiento de Señales Biomédicas (ECG / EEG)
Proyecto Final Informática II — Bioingeniería
"""

import numpy as np
import scipy.io as sio


class ModeloSenales:
    """
    Gestiona la carga y procesamiento de señales biomédicas almacenadas
    en archivos .mat (formato MATLAB). Soporta señales ECG y EEG.
    """

    def __init__(self):
        self.señal_3d = None        # Tensor original tal como viene del .mat
        self.señal_2d = None        # Reshape a 2D: (canales, muestras)
        self.nombre_archivo = ""
        self.fs = 1.0               # Frecuencia de muestreo (Hz), si está disponible

    # ---------------------------------------------------------------
    # 1. CARGA DEL ARCHIVO .MAT
    # ---------------------------------------------------------------
    def cargar_mat(self, ruta_archivo):
        """
        Carga un archivo .mat y extrae la primera variable numérica que encuentre.
        Guarda la forma original (3D si aplica) y un reshape a 2D.
        Retorna (True, mensaje) o (False, mensaje_error).
        """
        try:
            contenido = sio.loadmat(ruta_archivo)
            self.nombre_archivo = ruta_archivo

            # Buscamos la primera clave que no sea metadato de MATLAB
            claves_datos = [k for k in contenido if not k.startswith("__")]
            if not claves_datos:
                return False, "El archivo .mat no contiene variables de datos."

            datos = contenido[claves_datos[0]]
            if not isinstance(datos, np.ndarray):
                return False, "La variable encontrada no es un arreglo numérico."

            # Guardamos el tensor original
            self.señal_3d = datos.astype(np.float64)

            # Hacemos reshape a 2D: la convención es (canales, muestras)
            if datos.ndim == 1:
                self.señal_2d = datos.reshape(1, -1)
            elif datos.ndim == 2:
                # Si tiene más columnas que filas, asumimos (canales, muestras)
                if datos.shape[0] > datos.shape[1]:
                    self.señal_2d = datos.T
                else:
                    self.señal_2d = datos
            elif datos.ndim == 3:
                # Para EEG 3D: (epochs, canales, muestras) → (canales, epochs*muestras)
                ep, ch, sm = datos.shape
                self.señal_2d = datos.reshape(ch, ep * sm)
            else:
                self.señal_2d = datos.reshape(datos.shape[0], -1)

            return True, f"Señal cargada: {self.señal_2d.shape[0]} canales, {self.señal_2d.shape[1]} muestras."
        except Exception as e:
            return False, f"Error al cargar el archivo: {str(e)}"

    # ---------------------------------------------------------------
    # 2. SELECCIÓN Y RECORTE DE CANAL
    # ---------------------------------------------------------------
    def obtener_canal(self, indice_canal, muestra_inicio=0, muestra_fin=None):
        """
        Devuelve el segmento de un canal específico de la señal 2D.
        Si no se especifica muestra_fin, retorna hasta el final.
        """
        if self.señal_2d is None:
            return None

        indice_canal = max(0, min(indice_canal, self.señal_2d.shape[0] - 1))
        canal = self.señal_2d[indice_canal, :]

        if muestra_fin is None or muestra_fin > len(canal):
            muestra_fin = len(canal)

        return canal[muestra_inicio:muestra_fin]

    def obtener_num_canales(self):
        if self.señal_2d is None:
            return 0
        return self.señal_2d.shape[0]

    def obtener_num_muestras(self):
        if self.señal_2d is None:
            return 0
        return self.señal_2d.shape[1]

    # ---------------------------------------------------------------
    # 3. INYECCIÓN DE RUIDO
    # ---------------------------------------------------------------
    def agregar_ruido_gaussiano(self, indice_canal, desviacion=0.05):
        """
        Toma un canal de la señal 2D y le suma ruido blanco gaussiano.
        Retorna una tupla (señal_original, señal_ruidosa) para graficarlas.
        desviacion: std del ruido relativa a la amplitud de la señal.
        """
        canal_original = self.obtener_canal(indice_canal)
        if canal_original is None:
            return None, None

        # El ruido se escala por la amplitud de la señal para que sea coherente
        amplitud = np.ptp(canal_original)  # peak-to-peak
        ruido = np.random.normal(0, desviacion * amplitud, size=canal_original.shape)
        canal_ruidoso = canal_original + ruido

        return canal_original, canal_ruidoso

    # ---------------------------------------------------------------
    # 4. ANÁLISIS ESTADÍSTICO EN 3D
    # ---------------------------------------------------------------
    def calcular_estadisticas_3d(self, eje):
        """
        Calcula la media y desviación estándar del tensor 3D a lo largo de un eje.
        eje: 0, 1 o 2 — seleccionado por el usuario desde QRadioButtons.
        Retorna (promedio, desviacion, nombre_eje, unidades).
        """
        if self.señal_3d is None:
            return None, None, "", ""

        if eje >= self.señal_3d.ndim:
            eje = 0

        promedio   = np.mean(self.señal_3d, axis=eje)
        desviacion = np.std(self.señal_3d, axis=eje)

        # Nombres descriptivos para cada eje según convención EEG/ECG
        nombres_ejes = {
            0: ("Eje 0 (Epochs/Tiempo)",   "μV (promedio por epoch)"),
            1: ("Eje 1 (Canales)",          "μV (promedio por canal)"),
            2: ("Eje 2 (Muestras/Tiempo)", "μV (promedio por muestra)"),
        }
        nombre, unidades = nombres_ejes.get(eje, (f"Eje {eje}", "u.a."))

        return promedio.flatten(), desviacion.flatten(), nombre, unidades
