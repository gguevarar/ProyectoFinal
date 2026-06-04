# Vista de login

import os

from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi

from config import UI_DIR


class LoginView(QMainWindow):
    def __init__(self):
        super().__init__()
        ruta_ui = os.path.join(UI_DIR, "login.ui")
        loadUi(ruta_ui, self)

        if hasattr(self, "labelMensaje"):
            self.labelMensaje.setText("")

    def obtener_credenciales(self): # Devuelve el usuario y contrasena escritos
        usuario = self.lineEditUsuario.text().strip()
        password = self.lineEditPassword.text()
        return usuario, password

    def mostrar_mensaje(self, texto, error=True): # Muestra un mensaje debajo del formulario
        if hasattr(self, "labelMensaje"):
            color = "#c0392b" if error else "#27ae60"
            self.labelMensaje.setStyleSheet(f"color: {color};")
            self.labelMensaje.setText(texto)

    def limpiar(self): # Limpia los campos del formulario
        self.lineEditUsuario.clear()
        self.lineEditPassword.clear()
        if hasattr(self, "labelMensaje"):
            self.labelMensaje.setText("")
