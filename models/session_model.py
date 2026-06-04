# Modelo de sesión, sirve para guardar la foto de la camara en la base de datos

from datetime import datetime

from models.database import Database


class SessionModel:
    def __init__(self, database=None):
        self.db = database or Database()

    def registrar_sesion(self, id_usuario, ruta_foto, fecha=None): # Inserta un registro de sesion
        if fecha is None:
            fecha = datetime.now()

        query = (
            "INSERT INTO sesiones (id_usuario, ruta_foto, fecha_sesion) "
            "VALUES (%s, %s, %s)"
        )
        return self.db.execute(query, (id_usuario, ruta_foto, fecha))
