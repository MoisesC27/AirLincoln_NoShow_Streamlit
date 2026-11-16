"""Contrato de datos del archivo de pasajeros y revisión de tipos.

Solo usa pandas/numpy para que el pipeline (GitHub Actions) lo pueda correr sin Streamlit.
El detalle humano del contrato está en contrato-datos.md; este módulo es la versión que se ejecuta.

Decisiones sobre celdas vacías (propuesta del equipo, ver contrato-datos.md):
- "sin_dato": el valor no se conoce. La fila se excluye del análisis y se reporta.
- "no_aplica": la columna no se usa en el tablero ni en el modelo; el vacío se conserva como vacío.
- "recalcular": columna derivada de otras dos; si viene vacía se recalcula con sus componentes
  (da 0 cuando no se cumplen ambas condiciones).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# Textos que el archivo podría usar para decir "no hay dato". Se convierten a vacío (NaN) antes de revisar tipos.
MISSING_TOKENS = {"", "na", "n/a", "nan", "null", "none", "-", "--", "?", "#n/a", "sin dato", "s/d"}
INVISIBLE = ["﻿", "​", "\xa0"]  # BOM, espacio de ancho cero, espacio duro

B = {0, 1}
CONTRACT = [
    # columna, valores válidos, unidad, origen, qué significa vacío
    ("Customer_ID", None, "identificador", "archivo", "sin_dato"),
    ("No_Show", B, "0 = se presentó, 1 = no se presentó", "archivo", "sin_dato"),
    ("Major_Hub_Departure", B, "0/1", "archivo", "sin_dato"),
    ("Departure_Day", set(range(1, 8)), "1 = lunes … 7 = domingo", "archivo", "sin_dato"),
    ("Departure_Hour", {1, 2, 3}, "1 = mañana, 2 = tarde, 3 = noche", "archivo", "sin_dato"),
    ("Connections", B, "0/1", "archivo", "sin_dato"),
    ("International_Flight", B, "0/1", "archivo", "sin_dato"),
    ("Connection___International_Fligh", B, "0/1 (derivada)", "archivo", "recalcular"),
    ("Business_Traveler", B, "0/1", "archivo", "sin_dato"),
    ("Booking_Class", {1, 2, 3}, "1 = Primera, 2 = Business, 3 = Coach", "archivo", "sin_dato"),
    ("When_Ticket_Purchased", {1, 2, 3}, "1 = 2+ semanas, 2 = < 2 semanas, 3 = mismo día", "archivo", "sin_dato"),
    ("Age", set(range(1, 9)), "rango de edad 1–8", "archivo", "sin_dato"),
    ("Gender___Female", B, "0/1", "archivo", "no_aplica"),
    ("Frequent_Flier_Status", B, "0/1", "archivo", "sin_dato"),
    ("Weather_Issues", B, "0/1", "archivo", "sin_dato"),
    ("Weather_Issues___Connection", B, "0/1 (derivada)", "archivo", "recalcular"),
]
COLUMNS = [c[0] for c in CONTRACT]
# Columnas opcionales: si vienen, se revisan; si no vienen, el tablero funciona por día de la semana.
OPTIONAL = [
    ("Flight_Number", "texto", "número de vuelo del itinerario (ej. AL 106)", "archivo"),
    ("Flight_Date", "fecha", "fecha del vuelo AAAA-MM-DD; su día de la semana debe ser Departure_Day", "archivo"),
]
OPTIONAL_COLUMNS = [c[0] for c in OPTIONAL]
DERIVED = {
    "Connection___International_Fligh": ("Connections", "International_Flight"),
    "Weather_Issues___Connection": ("Weather_Issues", "Connections"),
}


class ContractError(Exception):
    def __init__(self, message: str, report: pd.DataFrame | None = None):
        super().__init__(message)
        self.report = report


@dataclass
class ContractResult:
    df: pd.DataFrame                 # datos limpios con columnas numéricas
    report: pd.DataFrame             # una fila por columna: tipo esperado/detectado, problemas, estado
    ok: bool
    invisible_rows: int = 0
    excluded_rows: int = 0
    recalculated: dict = field(default_factory=dict)
    missing_tokens_found: dict = field(default_factory=dict)
    problems: list = field(default_factory=list)
    invalid_rows: int = 0            # filas con algún valor inválido (se excluyen y se reportan)
    error_rows: list = field(default_factory=list)  # número de fila en el archivo (como en Excel) de las filas con error
    usable: bool = True              # False solo si faltan columnas o no quedan filas: entonces no se puede analizar


def _clean_text(s: pd.Series) -> pd.Series:
    s = s.astype("string")
    for ch in INVISIBLE:
        s = s.str.replace(ch, "", regex=False)
    return s.str.replace('"', "", regex=False).str.strip()


def check(raw: pd.DataFrame, vuelos: pd.DataFrame | None = None) -> ContractResult:
    """Revisa el archivo contra el contrato. No lanza excepción: devuelve el reporte y ok=False si algo falla."""
    problems = []
    raw = raw.copy()
    raw.columns = [str(c) for c in raw.columns]
    for ch in INVISIBLE:
        raw.columns = [c.replace(ch, "") for c in raw.columns]
    raw.columns = [c.strip().strip('"') for c in raw.columns]

    missing_cols = [c for c in COLUMNS if c not in raw.columns]
    extra_cols = [c for c in raw.columns if c not in COLUMNS and c not in OPTIONAL_COLUMNS]
    if missing_cols:
        problems.append("Faltan columnas: " + ", ".join(missing_cols))
    if extra_cols:
        problems.append("Columnas no declaradas en el contrato: " + ", ".join(extra_cols))

    invisible_rows = 0
    present = [c for c in COLUMNS if c in raw.columns]
    if present:
        txt = raw[present].astype("string")
        mask = pd.Series(False, index=raw.index)
        for ch in INVISIBLE:
            mask |= txt.apply(lambda s: s.str.contains(ch, regex=False, na=False)).any(axis=1)
        invisible_rows = int(mask.sum())

    clean = pd.DataFrame(index=raw.index)
    err_mask = pd.Series(False, index=raw.index)
    tokens_found, rows = {}, []
    for col, valid, unit, origin, empty in CONTRACT:
        if col not in raw.columns:
            rows.append(dict(columna=col, tipo_esperado="entero", tipo_detectado="falta", texto_no_numerico=0,
                             vacios=0, fuera_de_rango=0, vacio_significa=empty, estado="✕ Falta"))
            continue
        s = _clean_text(raw[col])
        is_token = s.str.lower().isin(MISSING_TOKENS) | s.isna()
        n_tokens = int(is_token.sum())
        if n_tokens:
            tokens_found[col] = sorted(set(s[is_token].fillna("<vacío>").replace("", "<vacío>").tolist()))
        s = s.mask(is_token)
        num = pd.to_numeric(s, errors="coerce")
        text_bad = int((num.isna() & s.notna()).sum())          # texto que no es número ni marca de vacío
        non_int = int((num.notna() & (num % 1 != 0)).sum())
        out_range = int((num.notna() & ~num.isin(valid)).sum()) if valid is not None else 0
        invalid = (num.isna() & s.notna()) | (num.notna() & (num % 1 != 0))
        if valid is not None:
            invalid |= num.notna() & ~num.isin(valid)
        err_mask |= invalid.fillna(False).astype(bool)
        clean[col] = num.mask(invalid)  # un valor inválido no se usa: la fila se excluye y se reporta
        detected = "texto" if text_bad else ("decimal" if non_int else "entero")
        bad = text_bad or non_int or out_range
        rows.append(dict(columna=col, tipo_esperado="entero", tipo_detectado=detected, texto_no_numerico=text_bad,
                         vacios=n_tokens, fuera_de_rango=out_range, vacio_significa=empty,
                         estado="✕ No cumple" if bad else "✓ Cumple"))
        if text_bad:
            ejemplos = s[num.isna() & s.notna()].unique()[:3].tolist()
            problems.append(f"{col}: {text_bad} valores con texto en una columna numérica (ej. {ejemplos})")
        if non_int:
            problems.append(f"{col}: {non_int} valores con decimales en una columna entera")
        if out_range:
            problems.append(f"{col}: {out_range} valores fuera de los códigos permitidos")

    report = pd.DataFrame(rows)
    recalculated, excluded = {}, 0
    if not missing_cols:
        for col, (a, b) in DERIVED.items():
            m = clean[col].isna() & clean[a].notna() & clean[b].notna()
            if m.any():
                clean.loc[m, col] = ((clean.loc[m, a] == 1) & (clean.loc[m, b] == 1)).astype(int)
                recalculated[col] = int(m.sum())
            ok_mask = clean[col].notna() & clean[a].notna() & clean[b].notna()
            expected = ((clean[a] == 1) & (clean[b] == 1)).fillna(False).astype(int)
            incoh_mask = (ok_mask & (clean[col] != expected)).fillna(False).astype(bool)
            incoh = int(incoh_mask.sum())
            err_mask |= incoh_mask
            clean.loc[incoh_mask, col] = pd.NA
            if incoh:
                problems.append(f"{col}: {incoh} filas no coinciden con {a} y {b}")
                report.loc[report.columna == col, "estado"] = "✕ No cumple"
        opt_err = _check_optional(raw, clean, vuelos, report_rows := [], problems)
        err_mask |= opt_err
        if report_rows:
            report = pd.concat([report, pd.DataFrame(report_rows)], ignore_index=True)
        sin_dato = [c for c, *_, e in CONTRACT if e in ("sin_dato", "recalcular")]
        drop = clean[sin_dato].isna().any(axis=1) | opt_err
        excluded = int(drop.sum())
        clean = clean[~drop].copy()
        int_cols = [c for c, *_, e in CONTRACT if e != "no_aplica"]
        clean[int_cols] = clean[int_cols].astype("int64")
        clean["Gender___Female"] = clean["Gender___Female"].astype("Int64")
        for c in OPTIONAL_COLUMNS:
            if c in clean.columns:
                clean[c] = clean[c].astype(object).where(clean[c].notna(), None)

    still_text = [c for c in clean.columns if c not in OPTIONAL_COLUMNS and not pd.api.types.is_numeric_dtype(clean[c])]
    if still_text:
        problems.append("Columnas que siguen como texto: " + ", ".join(still_text))
    ok = not problems
    clean.attrs["bom_rows"] = invisible_rows
    error_rows = [int(i) + 2 for i in raw.index[err_mask]]  # +2: encabezado y conteo desde 1, como en Excel
    usable = (not missing_cols) and len(clean) > 0
    return ContractResult(clean, report, ok, invisible_rows, excluded, recalculated, tokens_found, problems,
                          int(err_mask.sum()), error_rows, usable)


def _franja(hhmm: str) -> int:
    h = int(str(hhmm).split(":")[0])
    return 1 if 6 <= h < 12 else 2 if 12 <= h < 18 else 3


def _check_optional(raw, clean, vuelos, report_rows, problems) -> pd.Series:
    """Revisa Flight_Number y Flight_Date si vienen. Devuelve las filas con error (se excluyen y se reportan)."""
    err = pd.Series(False, index=raw.index)
    def add(col, tipo, detected, n_bad, n_empty, ok):
        report_rows.append(dict(columna=col, tipo_esperado=tipo, tipo_detectado=detected, texto_no_numerico=0, vacios=n_empty,
                                fuera_de_rango=n_bad, vacio_significa="no_aplica", estado="✓ Cumple" if ok else "✕ No cumple"))
    if "Flight_Date" in raw.columns:
        s = _clean_text(raw["Flight_Date"])
        s = s.mask(s.str.lower().isin(MISSING_TOKENS) | s.isna())
        dt = pd.to_datetime(s.str[:10], format="%Y-%m-%d", errors="coerce")
        bad = s.notna() & dt.isna()
        wd = (dt.dt.weekday + 1).astype("Float64")
        incoh = dt.notna() & clean["Departure_Day"].notna() & (wd != clean["Departure_Day"]).fillna(False)
        incoh = incoh.fillna(False).astype(bool)
        if bad.any():
            problems.append(f"Flight_Date: {int(bad.sum())} fechas que no se pueden leer (ej. {s[bad].unique()[:3].tolist()}); formato AAAA-MM-DD")
        if incoh.any():
            problems.append(f"Flight_Date: {int(incoh.sum())} filas cuya fecha no cae en el día de Departure_Day")
        err |= bad | incoh
        clean["Flight_Date"] = dt.dt.strftime("%Y-%m-%d").where(dt.notna() & ~incoh)
        add("Flight_Date", "fecha", "fecha" if not bad.any() else "texto", int(bad.sum() + incoh.sum()), int(s.isna().sum()), not (bad.any() or incoh.any()))
    if "Flight_Number" in raw.columns:
        s = _clean_text(raw["Flight_Number"]).str.upper()
        s = s.mask(s.str.lower().isin(MISSING_TOKENS) | s.isna())
        m = s.str.extract(r"^AL\s*-?\s*(\d{1,4})$")[0]
        norm = ("AL " + m).where(m.notna())
        bad = s.notna() & norm.isna()
        if bad.any():
            problems.append(f"Flight_Number: {int(bad.sum())} números de vuelo con formato inválido (ej. {s[bad].unique()[:3].tolist()}); formato AL 123")
        unknown = pd.Series(False, index=raw.index)
        incoh = pd.Series(False, index=raw.index)
        if vuelos is not None and len(vuelos):
            v = vuelos.copy()
            v["vuelo"] = v["vuelo"].astype(str).str.strip().str.upper()
            v = v.drop_duplicates("vuelo").set_index("vuelo")
            known = norm.isin(v.index)
            unknown = norm.notna() & ~known
            if unknown.any():
                problems.append(f"Flight_Number: {int(unknown.sum())} vuelos que no están en el itinerario (ej. {norm[unknown].unique()[:3].tolist()})")
            k = norm.where(known)
            fr = k.map(lambda x: _franja(v.at[x, "salida"]) if isinstance(x, str) else np.nan)
            hub = k.map(lambda x: int(v.at[x, "sale_de_hub"]) if isinstance(x, str) else np.nan)
            intl = k.map(lambda x: int(v.at[x, "internacional"]) if isinstance(x, str) else np.nan)
            dias = k.map(lambda x: str(v.at[x, "dias"]) if isinstance(x, str) else None)
            day_ok = pd.Series([not isinstance(d, str) or pd.isna(dd) or str(int(dd)) in d for d, dd in zip(dias, clean["Departure_Day"])], index=raw.index)
            incoh = known & ((fr != clean["Departure_Hour"]) | (hub != clean["Major_Hub_Departure"])
                             | (intl != clean["International_Flight"]) | ~day_ok).fillna(False)
            incoh = incoh.astype(bool)
            if incoh.any():
                problems.append(f"Flight_Number: {int(incoh.sum())} filas cuyo vuelo no coincide con su día, horario, hub o destino")
        err |= bad | unknown | incoh
        clean["Flight_Number"] = norm.where(~(bad | unknown | incoh))
        nb = int((bad | unknown | incoh).sum())
        add("Flight_Number", "texto", "texto", nb, int(s.isna().sum()), nb == 0)
    return err.fillna(False).astype(bool)


def read_bytes(data: bytes, name: str) -> pd.DataFrame:
    """Lee un CSV o Excel (bytes) como texto, sin convertir nada, para que el contrato decida."""
    import io
    low = name.lower()
    if low.endswith((".xlsx", ".xlsm", ".xls")):
        xl = pd.ExcelFile(io.BytesIO(data))
        sheet = "Pasajeros" if "Pasajeros" in xl.sheet_names else 0
        raw = pd.read_excel(xl, sheet_name=sheet, dtype=str, keep_default_na=False)
    else:
        text = None
        for enc in ("utf-8-sig", "latin-1"):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        sep = ";" if text.splitlines()[0].count(";") > text.splitlines()[0].count(",") else ","
        raw = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False, sep=sep)
    return raw.fillna("")


def read_vuelos(data: bytes, name: str) -> pd.DataFrame | None:
    """Itinerario: hoja «Vuelos» del Excel si existe; si no, data/vuelos.csv del proyecto."""
    import io
    if name.lower().endswith((".xlsx", ".xlsm", ".xls")):
        xl = pd.ExcelFile(io.BytesIO(data))
        if "Vuelos" in xl.sheet_names:
            return pd.read_excel(xl, sheet_name="Vuelos", dtype=str, keep_default_na=False)
    default = Path(__file__).resolve().parents[1] / "data" / "vuelos.csv"
    return pd.read_csv(default, dtype=str, keep_default_na=False) if default.exists() else None


def check_bytes(data: bytes, name: str) -> ContractResult:
    raw = read_bytes(data, name)
    vuelos = read_vuelos(data, name) if "Flight_Number" in [str(c).strip() for c in raw.columns] else None
    return check(raw, vuelos)


def read_and_check(path: Path) -> ContractResult:
    return check_bytes(Path(path).read_bytes(), Path(path).name)


def contract_table() -> pd.DataFrame:
    meaning = {"sin_dato": "Sin dato: la fila se excluye y se reporta",
               "no_aplica": "No aplica: no se usa en el tablero; se deja vacío",
               "recalcular": "Se recalcula con sus dos componentes (0 si no se cumplen ambos)"}
    rows = [{"Columna": c, "Tipo": "entero", "Unidad": u, "Origen": o, "Vacío significa": meaning[e]} for c, _, u, o, e in CONTRACT]
    rows += [{"Columna": c + " (opcional)", "Tipo": tp, "Unidad": u, "Origen": o, "Vacío significa": "Se deja vacío; la fila se conserva"}
             for c, tp, u, o in OPTIONAL]
    return pd.DataFrame(rows)
