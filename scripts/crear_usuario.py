"""Genera la sal y el hash de una contraseña para .streamlit/secrets.toml.

Uso:  python scripts/crear_usuario.py laura
Pide la contraseña sin mostrarla y escribe el bloque que hay que pegar en secrets.toml.
"""
import getpass
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.auth import hash_password  # noqa: E402

user = (sys.argv[1] if len(sys.argv) > 1 else input("Usuario: ")).strip().lower()
pw = getpass.getpass("Contraseña nueva: ")
if pw != getpass.getpass("Repite la contraseña: "):
    sys.exit("Las contraseñas no coinciden.")
salt = secrets.token_hex(16)
print(f'\n[usuarios.{user}]\nnombre = "{user.capitalize()}"\nsalt = "{salt}"\nhash = "{hash_password(pw, salt)}"\n')
