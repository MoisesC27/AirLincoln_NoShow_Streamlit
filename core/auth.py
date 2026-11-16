"""Inicio de sesión para los 3 usuarios del tablero (Laura, Armando y Anna).

Las contraseñas NO están en el código: en .streamlit/secrets.toml se guarda, por usuario, una sal y el hash
PBKDF2-SHA256 de su contraseña. Para crear o cambiar una contraseña: python scripts/crear_usuario.py <usuario>.
"Recordarme" guarda en la dirección de la página un token firmado (HMAC) que vence a los 7 días.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import time

import streamlit as st

ITERATIONS = 200_000
TOKEN_DAYS = 7
MAX_ATTEMPTS = 5


def hash_password(password: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), ITERATIONS).hex()


def _users() -> dict:
    try:
        return {k.lower(): dict(v) for k, v in dict(st.secrets.get("usuarios", {})).items()}
    except Exception:  # noqa: BLE001  (no existe secrets.toml)
        return {}


def configured() -> bool:
    return bool(_users())


def verify(username: str, password: str) -> dict | None:
    """Devuelve los datos del usuario si usuario y contraseña coinciden; si no, None."""
    u = _users().get((username or "").strip().lower())
    if not u or not password:
        hash_password("x", "00" * 16)  # mismo costo de tiempo aunque el usuario no exista
        return None
    if hmac.compare_digest(hash_password(password, u["salt"]), u["hash"]):
        return {"usuario": username.strip().lower(), "nombre": u.get("nombre", username), "rol": u.get("rol", "")}
    return None


def _secret() -> bytes:
    try:
        return str(st.secrets["auth_secret"]).encode()
    except Exception:  # noqa: BLE001
        return b""


def make_token(username: str) -> str:
    exp = int(time.time()) + TOKEN_DAYS * 86400
    msg = f"{username}|{exp}"
    sig = hmac.new(_secret(), msg.encode(), hashlib.sha256).hexdigest()[:32]
    return base64.urlsafe_b64encode(f"{msg}|{sig}".encode()).decode()


def read_token(token: str) -> dict | None:
    if not token or not _secret():
        return None
    try:
        username, exp, sig = base64.urlsafe_b64decode(token.encode()).decode().split("|")
    except Exception:  # noqa: BLE001
        return None
    good = hmac.new(_secret(), f"{username}|{exp}".encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, good) or int(exp) < time.time():
        return None
    u = _users().get(username)
    return {"usuario": username, "nombre": u.get("nombre", username), "rol": u.get("rol", "")} if u else None
