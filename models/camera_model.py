# Modelo para la camara

import os
from datetime import datetime

import cv2

from config import CAPTURES_DIR

class CameraModel:
    def __init__(self, indice_camara=0):
        self.indice_camara = indice_camara
        self.captura = None

    def abrir(self): # Abre la camara
        self.captura = cv2.VideoCapture(self.indice_camara, cv2.CAP_DSHOW)
        if not self.captura.isOpened():
            self.captura = None
            return False
        return True

    def esta_abierta(self): # Verifica si la camara esta abierta
        return self.captura is not None and self.captura.isOpened()

    def leer_frame(self): # Lee un fotograma de la camara
        if not self.esta_abierta():
            return None
        ok, frame = self.captura.read()
        if not ok:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def guardar_foto(self, id_usuario): # Toma una foto y la guarda en disco
        if not self.esta_abierta():
            return None

        ok, frame = self.captura.read()
        if not ok:
            return None

        os.makedirs(CAPTURES_DIR, exist_ok=True)
        marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"usuario_{id_usuario}_{marca_tiempo}.jpg"
        ruta = os.path.join(CAPTURES_DIR, nombre_archivo)

        cv2.imwrite(ruta, frame)
        return ruta

    def cerrar(self): # Libera la camara
        if self.captura is not None:
            self.captura.release()
            self.captura = None
