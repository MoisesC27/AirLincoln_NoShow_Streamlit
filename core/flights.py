"""Itinerario de vuelos (data/vuelos.csv) para el calendario de Laura. Reglas en contrato-datos.md, sección D."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

PATH = Path(__file__).resolve().parents[1] / "data" / "vuelos.csv"
COLS = ["vuelo", "origen", "ciudad_origen", "destino", "ciudad_destino", "salida", "dias", "avion", "asientos",
        "sale_de_hub", "internacional"]


def franja(salida: str) -> int:
    """1 = mañana (6–12 h), 2 = tarde (12–18 h), 3 = noche (18–6 h), igual que Departure_Hour."""
    h = int(salida.split(":")[0])
    return 1 if 6 <= h < 12 else 2 if 12 <= h < 18 else 3


def check(df: pd.DataFrame) -> list[str]:
    """Lista de problemas; vacía si el itinerario cumple el contrato."""
    faltan = [c for c in COLS if c not in df.columns]
    if faltan:
        return [f"Faltan columnas: {', '.join(faltan)}"]
    p = []
    if df[COLS].isna().any().any():
        p.append("Hay celdas vacías")
    if not df["salida"].astype(str).str.fullmatch(r"([01]\d|2[0-3]):[0-5]\d").all():
        p.append("«salida» debe tener formato HH:MM")
    if not df["dias"].astype(str).map(lambda s: bool(re.fullmatch(r"[1-7]+", s))).all():
        p.append("«dias» solo admite dígitos 1 a 7 (1 = lunes)")
    asientos = pd.to_numeric(df["asientos"], errors="coerce")
    if asientos.isna().any() or (asientos % 1 != 0).any() or not asientos.between(20, 600).all():
        p.append("«asientos» debe ser entero entre 20 y 600")
    for c in ("sale_de_hub", "internacional"):
        if not pd.to_numeric(df[c], errors="coerce").isin([0, 1]).all():
            p.append(f"«{c}» solo admite 0 o 1")
    if df["vuelo"].duplicated().any():
        p.append("Hay números de vuelo repetidos")
    return p


def load(path: Path = PATH) -> tuple[list[list], list[str]]:
    """Vuelos como listas compactas para la plantilla y la lista de problemas encontrados."""
    if not path.exists():
        return [], [f"No se encontró {path.name}"]
    return from_df(pd.read_csv(path, dtype={"dias": str, "salida": str}))


def load_bytes(data: bytes, name: str) -> tuple[list[list], list[str]]:
    """Hoja «Vuelos» del archivo cargado si existe; si no, el itinerario del proyecto."""
    from .contract import read_vuelos
    df = read_vuelos(data, name)
    if df is None:
        return [], ["No hay itinerario de vuelos"]
    return from_df(df)


def from_df(df: pd.DataFrame) -> tuple[list[list], list[str]]:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for c in ("vuelo", "salida", "dias"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
    if "vuelo" in df.columns:
        df["vuelo"] = df["vuelo"].str.upper()
    probs = check(df)
    if probs:
        return [], probs
    out = [[r.vuelo, r.origen, r.ciudad_origen, r.destino, r.ciudad_destino, r.salida, r.dias, r.avion,
            int(float(r.asientos)), int(float(r.sale_de_hub)), int(float(r.internacional)), franja(r.salida)] for r in df.itertuples()]
    return out, []
