# Modelo para la camara

import os
from datetime import datetime

import cv2

from config import CAPTURES_DIR

class CameraModel:
    def __init__(self, indice_camara=0):
        self.indice_camara = indice_camara
        self.captura = None
        self.ultimo_frame = None

    def abrir(self): # Abre la camara
        self.captura = cv2.VideoCapture(self.indice_camara, cv2.CAP_DSHOW)
        if not self.captura.isOpened():
            self.captura = None
            return False
        return True

    def esta_abierta(self): # Verifica si la camara esta abierta
        return self.captura is not None and self.captura.isOpened()

    def leer_frame(self): # Lee un fotograma y guarda el ultimo valido
        if not self.esta_abierta():
            return None
        ok, frame = self.captura.read()
        if not ok:
            return None
        self.ultimo_frame = frame
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def guardar_foto(self, id_usuario): # Guarda en disco el ultimo fotograma del video
        frame = self.ultimo_frame
        if frame is None and self.esta_abierta():
            ok, frame = self.captura.read()
            if not ok:
                frame = None

        if frame is None:
            return None

        os.makedirs(CAPTURES_DIR, exist_ok=True)
        marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"usuario_{id_usuario}_{marca_tiempo}.jpg"
        ruta = os.path.join(CAPTURES_DIR, nombre_archivo)

        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            return None
        try:
            with open(ruta, "wb") as archivo:
                archivo.write(buffer.tobytes())
        except OSError:
            return None
        return ruta

    def cerrar(self): # Cierra la camara
        if self.captura is not None:
            self.captura.release()
            self.captura = None
        self.ultimo_frame = None