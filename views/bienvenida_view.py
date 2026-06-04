# Vista de bienvenida, sirve para mostrar la pantalla de bienvenida

import os

from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi

from config import UI_DIR


class BienvenidaView(QMainWindow):
    def __init__(self):
        super().__init__()
        ruta_ui = os.path.join(UI_DIR, "bienvenida.ui")
        loadUi(ruta_ui, self)
