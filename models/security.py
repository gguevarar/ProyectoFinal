# Modelo de seguridad, sirve para cifrar y verificar contraseñas

import hashlib
import hmac
import os

ALGORITMO = "sha256"
ITERACIONES = 200_000
PREFIJO = "pbkdf2_sha256"


def hash_password(password): # Devuelve el hash seguro de una contrasena
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(ALGORITMO, password.encode("utf-8"), salt, ITERACIONES)
    return f"{PREFIJO}${ITERACIONES}${salt.hex()}${dk.hex()}"


def verify_password(password, almacenado): # Compara una contrasena con el hash guardado
    try:
        prefijo, iteraciones, salt_hex, hash_hex = almacenado.split("$")
        iteraciones = int(iteraciones)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac(ALGORITMO, password.encode("utf-8"), salt, iteraciones)
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def is_hashed(almacenado): # Indica si el valor guardado ya esta cifrado
    return isinstance(almacenado, str) and almacenado.startswith(PREFIJO + "$")
