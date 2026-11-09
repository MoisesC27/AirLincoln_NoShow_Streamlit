"""Autenticación, autorización por rol, seudonimización y supresión de grupos pequeños.

- Autenticación: Streamlit OIDC (st.login) cuando .streamlit/secrets.toml tiene la sección [auth].
- Autorización: el rol se obtiene del correo verificado mediante la tabla [roles] de secrets.
  Sin sesión, el rol es "publico". Cada función que entrega datos individuales comprueba el permiso
  en el servidor antes de calcularlos; ocultar una pestaña no es el mecanismo de protección.
"""
from __future__ import annotations

import hashlib
import hmac

import pandas as pd
import streamlit as st

from .catalog import MIN_N

ROLES = {
    "publico": "Público (sin sesión)",
    "planificacion": "Planificación (Laura)",
    "experiencia": "Experiencia del pasajero (Armando)",
    "operacion": "Operación y calidad (Anna)",
    "admin": "Administración",
}

PERMISSIONS = {
    "ver_agregados": "Ver tasas agregadas (n ≥ 30) y métricas del modelo",
    "simular": "Usar el simulador de sobreventa",
    "ver_individual": "Ver lista priorizada de pasajeros (seudonimizada)",
    "ver_detalle_calidad": "Ver detalle de Customer_ID repetidos (seudonimizados)",
    "decidir_corte": "Registrar aceptación o bloqueo del corte",
    "exportar_agregados": "Descargar propuestas con datos agregados",
}

MATRIX = {
    "publico": {"ver_agregados", "simular"},
    "planificacion": {"ver_agregados", "simular", "exportar_agregados"},
    "experiencia": {"ver_agregados", "simular", "ver_individual", "exportar_agregados"},
    "operacion": {"ver_agregados", "simular", "ver_detalle_calidad", "decidir_corte", "exportar_agregados"},
    "admin": set(PERMISSIONS),
}
# Ningún rol puede exportar registros individuales: el permiso no existe.


def _secrets() -> dict:
    try:
        return dict(st.secrets)
    except Exception:  # noqa: BLE001  (no hay secrets.toml)
        return {}


def auth_configured() -> bool:
    s = _secrets()
    return "auth" in s


def current_user() -> tuple[str, str | None]:
    """(rol, correo). Sin autenticación configurada o sin sesión: ('publico', None)."""
    if not auth_configured():
        return "publico", None
    try:
        if not st.user.is_logged_in:
            return "publico", None
        email = str(st.user.get("email", "")).lower()
    except Exception:  # noqa: BLE001
        return "publico", None
    roles = {k.lower(): v for k, v in dict(_secrets().get("roles", {})).items()}
    role = roles.get(email, "publico")
    return (role if role in MATRIX else "publico"), email


def can(role: str, perm: str) -> bool:
    return perm in MATRIX.get(role, set())


def pseudonym(customer_id: int) -> str | None:
    """Identificador protegido (HMAC-SHA256 con sal secreta). Sin sal configurada no se generan IDs."""
    salt = _secrets().get("pseudonym_salt")
    if not salt:
        return None
    digest = hmac.new(str(salt).encode(), str(customer_id).encode(), hashlib.sha256).hexdigest()
    return "P-" + digest[:8].upper()


def suppress(table: pd.DataFrame, n_col: str = "registros", value_cols: tuple = ("tasa", "ausencias", "ic_bajo", "ic_alto")) -> pd.DataFrame:
    """Marca como suprimidas las filas con n < MIN_N y borra sus valores."""
    t = table.copy()
    t["suprimido"] = t[n_col] < MIN_N
    for c in value_cols:
        if c in t:
            t[c] = t[c].astype(float).where(~t["suprimido"])
    if "ausencias" in t:
        t["ausencias"] = t["ausencias"].round().astype("Int64")
    return t


def complementary_suppression(grid: pd.DataFrame, n_col: str = "registros", row: str = "Departure_Hour") -> pd.DataFrame:
    """Si en una fila del mapa queda una sola celda suprimida, suprime además la celda publicada más pequeña
    de esa fila, para que no pueda reconstruirse por diferencia con el total de la fila."""
    g = grid.copy()
    for _, idx in g.groupby(row).groups.items():
        sub = g.loc[idx]
        if sub["suprimido"].sum() == 1 and (~sub["suprimido"]).any():
            j = sub[~sub["suprimido"]][n_col].idxmin()
            g.loc[j, "suprimido"] = True
            g.loc[j, "complementaria"] = True
            for c in ("tasa", "ic_bajo", "ic_alto"):
                if c in g:
                    g.loc[j, c] = float("nan")
            if "ausencias" in g:
                g.loc[j, "ausencias"] = pd.NA
    if "complementaria" not in g:
        g["complementaria"] = False
    g["complementaria"] = g["complementaria"].fillna(False).astype(bool)
    return g
