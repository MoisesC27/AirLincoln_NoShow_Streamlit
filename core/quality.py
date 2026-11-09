"""Validaciones de calidad del corte de datos y regla de aceptación."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .catalog import EXPECTED_COLUMNS, FEATURES, ID_COL, TARGET
from .data import invalid_values

OK, WARN, FAIL = "Cumple", "Advertencia", "No cumple"
SEVERITY_ORDER = {"Crítica": 0, "Alta": 1, "Media": 2, "Baja": 3}

# Umbrales de aceptación (propuesta del equipo, pendiente de aprobación).
MIN_AUC_TEST = 0.75
MAX_ECE = 0.05
MAX_PSI = 0.25


def psi(a: pd.Series, b: pd.Series) -> float:
    ca = a.value_counts(normalize=True); cb = b.value_counts(normalize=True)
    idx = ca.index.union(cb.index)
    ca = ca.reindex(idx, fill_value=1e-4); cb = cb.reindex(idx, fill_value=1e-4)
    return float(((cb - ca) * np.log(cb / ca)).sum())


def psi_table(df: pd.DataFrame) -> pd.DataFrame:
    tr = df[df.part == "train"]; ot = df[df.part != "train"]
    rows = [{"variable": f, "psi": psi(tr[f], ot[f])} for f in FEATURES + [TARGET]]
    t = pd.DataFrame(rows)
    t["estado"] = np.where(t["psi"] < 0.10, "Estable", np.where(t["psi"] < MAX_PSI, "Vigilar", "Reentrenar"))
    return t


def run_checks(df: pd.DataFrame, metrics: pd.DataFrame, selected: str) -> pd.DataFrame:
    checks = []

    def add(nombre, resultado, estado, severidad, consecuencia, accion):
        checks.append(dict(validacion=nombre, resultado=resultado, estado=estado, severidad=severidad,
                           consecuencia=consecuencia, accion=accion))

    cols_ok = all(c in df.columns for c in EXPECTED_COLUMNS)
    add("Columnas esperadas", f"{len(EXPECTED_COLUMNS)} de {len(EXPECTED_COLUMNS)}" if cols_ok else "Faltan columnas",
        OK if cols_ok else FAIL, "Crítica", "Sin columnas el modelo no puede calcular probabilidades.",
        "Ninguna." if cols_ok else "Corregir el archivo de origen.")

    miss = int(df[EXPECTED_COLUMNS].isna().sum().sum())
    add("Valores faltantes", f"{miss:,} celdas vacías", OK if miss == 0 else FAIL, "Crítica",
        "Registros incompletos sesgan tasas y predicciones.", "Ninguna." if miss == 0 else "Completar o excluir con regla documentada.")

    bom = int(df.attrs.get("bom_rows", 0))
    add("Caracteres invisibles (BOM) en el archivo", f"{bom} filas corregidas al cargar",
        OK if bom == 0 else WARN, "Baja",
        "Indican que el CSV se unió desde varias partes; sin limpiarlos, esos Customer_ID se leen como vacíos.",
        "Ninguna." if bom == 0 else "Exportar el archivo de nuevo en una sola pieza.")

    bad = invalid_values(df)
    add("Valores dentro del diccionario", "Todos válidos" if not bad else "; ".join(f"{k}: {v}" for k, v in bad.items()),
        OK if not bad else FAIL, "Crítica", "Un código desconocido no tiene coeficiente en el modelo.",
        "Ninguna." if not bad else "Revisar códigos fuera de rango.")

    full_dup = int(df.drop(columns=["part"]).duplicated().sum())
    add("Filas idénticas (incluye Customer_ID)", f"{full_dup:,}", OK if full_dup == 0 else WARN, "Alta",
        "Duplicar un registro infla su peso en tasas y entrenamiento.", "Ninguna." if full_dup == 0 else "Eliminar duplicados exactos.")

    same_profile = int(df.drop(columns=["part", ID_COL]).duplicated().sum())
    add("Perfiles repetidos sin Customer_ID", f"{same_profile:,} filas",
        OK, "Baja",
        "Esperable: casi todas las variables son categóricas, así que pasajeros distintos comparten perfil.",
        "No eliminar; son pasajeros distintos (Entrega 3).")

    rep = df[ID_COL].value_counts()
    rep_ids = rep[rep > 1]
    add("Customer_ID repetidos con datos distintos", f"{len(rep_ids)} identificadores ({int(rep_ids.sum())} filas)",
        OK if len(rep_ids) == 0 else WARN, "Media",
        "Puede ser el mismo pasajero en viajes distintos o un error de captura.",
        "Confirmar con el área de reservaciones; se mantuvieron juntos en la partición.")

    parts = df.groupby("part")[ID_COL].apply(set)
    shared = len(parts.get("train", set()) & parts.get("valid", set())) + len(parts.get("train", set()) & parts.get("test", set())) \
        + len(parts.get("valid", set()) & parts.get("test", set()))
    add("Customer_ID compartidos entre particiones", f"{shared}", OK if shared == 0 else FAIL, "Crítica",
        "Un mismo pasajero en entrenamiento y prueba infla las métricas (fuga de información).",
        "Ninguna." if shared == 0 else "Rehacer la partición agrupando por Customer_ID.")

    wxc = bool(((df["Weather_Issues___Connection"] == 1) == ((df["Weather_Issues"] == 1) & (df["Connections"] == 1))).all())
    cxi = bool(((df["Connection___International_Fligh"] == 1) == ((df["Connections"] == 1) & (df["International_Flight"] == 1))).all())
    add("Variables combinadas coherentes", "Clima+conexión y conexión+internacional cuadran" if wxc and cxi else "Hay incoherencias",
        OK if wxc and cxi else FAIL, "Alta", "Una combinación incoherente contradice a sus componentes.",
        "Ninguna." if wxc and cxi else "Recalcular las variables combinadas.")

    rates = df.groupby("part")[TARGET].mean()
    spread = float(rates.max() - rates.min())
    add("Balance de No_Show entre particiones",
        " · ".join(f"{p}: {rates[p]:.1%}" for p in ("train", "valid", "test") if p in rates),
        OK if spread < 0.03 else WARN, "Media", "Particiones muy distintas hacen menos comparable la evaluación.",
        "Ninguna." if spread < 0.03 else "Revisar la estratificación.")

    add("Partition_ID del diccionario", "No viene en el archivo", WARN, "Baja",
        "No se puede reproducir exactamente la partición de Colab (5,999 / 3,001 / 1,000).",
        "Agregar data/particion.csv con la asignación oficial.")

    add("Clima conocido antes del vuelo", "No verificable con el dataset", WARN, "Alta",
        "Si Weather_Issues se registró después del vuelo, hay fuga temporal y las métricas son optimistas.",
        "Usar el pronóstico disponible al momento de predecir y documentar su hora.")

    ps = psi_table(df)
    mx = float(ps["psi"].max())
    add("Estabilidad de distribuciones (PSI)", f"Máximo {mx:.3f}", OK if mx < 0.10 else (WARN if mx < MAX_PSI else FAIL), "Alta",
        "Si los datos nuevos cambian, el modelo pierde precisión.", "Ninguna." if mx < 0.10 else "Vigilar y reentrenar si supera 0.25.")

    m = metrics[(metrics.modelo == selected) & (metrics.conjunto == "test")].iloc[0]
    add("Capacidad del modelo en prueba (AUC)", f"{m.auc:.3f} (mínimo {MIN_AUC_TEST})",
        OK if m.auc >= MIN_AUC_TEST else FAIL, "Crítica", "Con AUC bajo las alertas no distinguen a quien falta.",
        "Ninguna." if m.auc >= MIN_AUC_TEST else "No usar las predicciones; reentrenar.")
    add("Calibración en prueba (ECE)", f"{m.ece:.3f} (máximo {MAX_ECE})",
        OK if m.ece <= MAX_ECE else WARN, "Alta", "Probabilidades mal calibradas distorsionan el simulador de sobreventa.",
        "Ninguna." if m.ece <= MAX_ECE else "Recalibrar el modelo.")

    out = pd.DataFrame(checks)
    out["orden"] = out["severidad"].map(SEVERITY_ORDER)
    return out


def gate(checks: pd.DataFrame) -> tuple[str, list[str]]:
    """Regla: cualquier 'No cumple' de severidad Crítica bloquea el corte.
    Advertencias o fallas no críticas: aceptado con observaciones. Todo cumple: aceptado."""
    crit = checks[(checks.estado == FAIL) & (checks.severidad == "Crítica")]
    if len(crit):
        return "Bloqueado", [f"{r.validacion}: {r.resultado}" for r in crit.itertuples()]
    obs = checks[checks.estado != OK].sort_values("orden")
    if len(obs):
        return "Aceptado con observaciones", [f"{r.validacion} ({r.severidad}): {r.resultado}" for r in obs.itertuples()]
    return "Aceptado", []
