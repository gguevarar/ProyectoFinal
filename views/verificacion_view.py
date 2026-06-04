# Vista de verificacion por camara

import os

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
from PyQt5.uic import loadUi

from config import UI_DIR


class VerificacionView(QMainWindow):
    def __init__(self):
        super().__init__()
        ruta_ui = os.path.join(UI_DIR, "verificacion.ui")
        loadUi(ruta_ui, self)

    def mostrar_frame(self, frame_rgb): # Muestra el video de la camara en pantalla
        if frame_rgb is None or not hasattr(self, "labelCamara"):
            return
        alto, ancho, canales = frame_rgb.shape
        bytes_por_linea = canales * ancho
        imagen = QImage(
            frame_rgb.data, ancho, alto, bytes_por_linea, QImage.Format_RGB888
        )
        pixmap = QPixmap.fromImage(imagen)
        self.labelCamara.setPixmap(
            pixmap.scaled(
                self.labelCamara.width(),
                self.labelCamara.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def mostrar_estado(self, texto): # Muestra un mensaje de estado
        if hasattr(self, "labelEstado"):
            self.labelEstado.setText(texto)

    def reset(self): # Deja la ventana lista para una nueva verificacion
        if hasattr(self, "labelEstado"):
            self.labelEstado.setText("")
        if hasattr(self, "labelCamara"):
            self.labelCamara.clear()
            self.labelCamara.setText("Iniciando camara...")
