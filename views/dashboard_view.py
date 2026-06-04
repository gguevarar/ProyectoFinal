# Vista del dashboard, sirve para mostrar el panel principal después de verificar la sesión

import os

from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem
from PyQt5.uic import loadUi

from config import UI_DIR


class DashboardView(QMainWindow):
    def __init__(self):
        super().__init__()
        ruta_ui = os.path.join(UI_DIR, "dashboard.ui")
        loadUi(ruta_ui, self)

    def set_usuario(self, nombre, rol): # Muestra el saludo con el nombre y rol
        if hasattr(self, "labelBienvenidaUsuario"):
            self.labelBienvenidaUsuario.setText(
                f"Te damos la bienvenida, {nombre}  ({rol})"
            )

    def mostrar_pagina(self, pagina): # Cambia la pagina visible del area de contenido
        self.stackedContenido.setCurrentWidget(pagina)

    def cargar_usuarios(self, usuarios): # Llena la tabla con la lista de usuarios
        self.tableUsuarios.setRowCount(0)
        for usuario in usuarios:
            fila = self.tableUsuarios.rowCount()
            self.tableUsuarios.insertRow(fila)
            self.tableUsuarios.setItem(fila, 0, QTableWidgetItem(str(usuario.id)))
            self.tableUsuarios.setItem(fila, 1, QTableWidgetItem(usuario.nombre))
            self.tableUsuarios.setItem(fila, 2, QTableWidgetItem(usuario.rol))

    def obtener_datos_nuevo_usuario(self): # Devuelve los datos escritos en el formulario
        nombre = self.lineEditNuevoNombre.text().strip()
        password = self.lineEditNuevoPassword.text()
        rol = self.comboRol.currentText()
        return nombre, password, rol

    def mensaje_usuarios(self, texto, error=False): # Muestra un mensaje en la pagina de usuarios
        color = "#c0392b" if error else "#27ae60"
        self.labelMensajeUsuarios.setStyleSheet(f"color: {color};")
        self.labelMensajeUsuarios.setText(texto)

    def limpiar_form_usuario(self): # Limpia el formulario de creacion de usuario
        self.lineEditNuevoNombre.clear()
        self.lineEditNuevoPassword.clear()
        self.comboRol.setCurrentIndex(0)
