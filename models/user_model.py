# Modelo de usuario, sirve para validar el login, listar y crear usuarios

from mysql.connector import IntegrityError

from models.database import Database
from models.security import hash_password, verify_password, is_hashed


class Usuario:
    def __init__(self, id_usuario, nombre, rol):
        self.id = id_usuario
        self.nombre = nombre
        self.rol = rol

    def __repr__(self):
        return f"Usuario(id={self.id}, nombre={self.nombre!r}, rol={self.rol!r})"


class UserModel:
    def __init__(self, database=None):
        self.db = database or Database()

    def validar_login(self, usuario, password): # Comprueba usuario y contrasena contra la BD
        query = (
            "SELECT id, nombre, password, rol FROM usuarios "
            "WHERE (nombre = %s OR id = %s) LIMIT 1"
        )
        id_param = usuario if str(usuario).isdigit() else -1
        fila = self.db.fetch_one(query, (usuario, id_param))

        if not fila:
            return None

        guardado = fila["password"]

        if is_hashed(guardado):
            valido = verify_password(password, guardado)
        else:
            valido = password == guardado
            if valido:
                self._migrar_password(fila["id"], password)

        if valido:
            return Usuario(fila["id"], fila["nombre"], fila["rol"])
        return None

    def _migrar_password(self, id_usuario, password): # Cifra una contrasena antigua en texto plano
        try:
            self.db.execute(
                "UPDATE usuarios SET password = %s WHERE id = %s",
                (hash_password(password), id_usuario),
            )
        except Exception:
            pass

    def listar_usuarios(self): # Devuelve la lista de todos los usuarios
        filas = self.db.fetch_all("SELECT id, nombre, rol FROM usuarios ORDER BY id")
        return [Usuario(f["id"], f["nombre"], f["rol"]) for f in filas]

    def crear_usuario(self, nombre, password, rol): # Inserta un nuevo usuario con contrasena cifrada
        if rol not in ("administrador", "usuario"):
            rol = "usuario"

        query = "INSERT INTO usuarios (nombre, password, rol) VALUES (%s, %s, %s)"
        try:
            self.db.execute(query, (nombre, hash_password(password), rol))
            return True, "Usuario creado correctamente."
        except IntegrityError:
            return False, "Ya existe un usuario con ese nombre."
