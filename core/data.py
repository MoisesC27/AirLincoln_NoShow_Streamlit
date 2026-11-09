"""Carga, limpieza y partición del dataset."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from .catalog import EXPECTED_COLUMNS, ID_COL, RANDOM_STATE, TARGET, VALID_VALUES

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "AIRLINCOLNDATA2.csv"
PARTITION_FILE = ROOT / "data" / "particion.csv"  # opcional: asignación oficial (Customer_ID, conjunto)


class DataError(Exception):
    """Error de datos con un mensaje comprensible para la persona usuaria."""


@dataclass(frozen=True)
class DatasetInfo:
    file_name: str
    sha256: str
    rows: int
    columns: int
    loaded_at: str
    partition_source: str


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dataset(path: Path = DATA_FILE) -> pd.DataFrame:
    """Lee el CSV, quita comillas/espacios/BOM y convierte a enteros. Lanza DataError si algo no cuadra."""
    if not path.exists():
        raise DataError(f"No se encontró el archivo de datos: data/{path.name}.")
    try:
        raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    except Exception as exc:  # noqa: BLE001
        raise DataError(f"No se pudo leer data/{path.name}: {exc}") from exc
    raw.columns = [c.replace("﻿", "").strip().strip('"') for c in raw.columns]
    missing = [c for c in EXPECTED_COLUMNS if c not in raw.columns]
    if missing:
        raise DataError("Faltan columnas en el archivo: " + ", ".join(missing))
    sub = raw[EXPECTED_COLUMNS]
    bom_rows = int(sub.apply(lambda s: s.str.contains("\ufeff", regex=False, na=False)).any(axis=1).sum())
    df = sub.apply(lambda s: s.str.replace("\ufeff", "", regex=False).str.replace('"', "", regex=False).str.strip())
    df = df.apply(pd.to_numeric, errors="coerce")
    df.attrs["bom_rows"] = bom_rows
    return df


def invalid_values(df: pd.DataFrame) -> dict[str, int]:
    """Número de valores fuera del diccionario por columna."""
    out = {}
    for col, valid in VALID_VALUES.items():
        bad = (~df[col].isin(valid)).sum()
        if bad:
            out[col] = int(bad)
    return out


def assign_partition(df: pd.DataFrame) -> tuple[pd.Series, str]:
    """Asigna Entrenamiento/Validación/Prueba (60/30/10) manteniendo juntos los Customer_ID.

    Si existe data/particion.csv (Customer_ID, conjunto) se usa esa asignación oficial.
    Si no, se genera una partición estratificada por No_Show y agrupada por Customer_ID con semilla fija.
    """
    if PARTITION_FILE.exists():
        p = pd.read_csv(PARTITION_FILE)
        mapping = dict(zip(p[ID_COL], p["conjunto"].str.lower().map(
            {"training": "train", "entrenamiento": "train", "train": "train",
             "validation": "valid", "validación": "valid", "validacion": "valid", "valid": "valid",
             "test": "test", "prueba": "test"})))
        part = df[ID_COL].map(mapping)
        if part.isna().any():
            raise DataError("data/particion.csv no cubre todos los Customer_ID del dataset.")
        return part, "Archivo data/particion.csv"
    folds = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=RANDOM_STATE)
    part = pd.Series(index=df.index, dtype=object)
    for i, (_, idx) in enumerate(folds.split(df, df[TARGET], groups=df[ID_COL])):
        part.iloc[idx] = "train" if i < 6 else ("valid" if i < 9 else "test")
    return part, f"Generada: estratificada por No_Show y agrupada por Customer_ID (semilla {RANDOM_STATE})"


def prepare(path: Path = DATA_FILE) -> tuple[pd.DataFrame, DatasetInfo]:
    df = load_dataset(path)
    if df.isna().any().any():
        n = int(df.isna().sum().sum())
        raise DataError(f"El archivo tiene {n} valores vacíos o no numéricos; corrige el archivo antes de continuar.")
    bom_rows = df.attrs.get("bom_rows", 0)
    df = df.astype(int)
    df.attrs["bom_rows"] = bom_rows
    df["part"], source = assign_partition(df)
    info = DatasetInfo(
        file_name=path.name,
        sha256=file_hash(path),
        rows=len(df),
        columns=len(EXPECTED_COLUMNS),
        loaded_at=pd.Timestamp.now(tz="America/Mexico_City").strftime("%Y-%m-%d %H:%M"),
        partition_source=source,
    )
    return df, info


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confianza de Wilson al 95% para una proporción k/n."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z**2 / n
    c = (p + z**2 / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return (max(0.0, c - h), min(1.0, c + h))


def rate_table(df: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Tasa observada de no-show por grupo con numerador, denominador e IC 95%."""
    g = df.groupby(by, observed=True)[TARGET].agg(ausencias="sum", registros="size").reset_index()
    g["tasa"] = g["ausencias"] / g["registros"]
    ci = [wilson(k, n) for k, n in zip(g["ausencias"], g["registros"])]
    g["ic_bajo"] = [c[0] for c in ci]
    g["ic_alto"] = [c[1] for c in ci]
    return g
