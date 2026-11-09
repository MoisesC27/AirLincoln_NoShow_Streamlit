"""Contexto compartido: datos, modelos y validaciones, calculados una vez y guardados en caché."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from .catalog import TARGET
from .data import DATA_FILE, DatasetInfo, prepare
from .model import TrainedModels, reference_logits, train_all
from .quality import gate, run_checks


@dataclass
class Context:
    df: pd.DataFrame
    info: DatasetInfo
    tm: TrainedModels
    p: pd.Series            # probabilidad del modelo seleccionado
    checks: pd.DataFrame
    gate_status: str
    gate_reasons: list
    overall: float
    overall_k: int
    ref_logits: dict
    t_rec: float


@st.cache_resource(show_spinner="Cargando datos y entrenando los 5 modelos (solo la primera vez)…")
def _build(mtime: float, size: int) -> Context:  # mtime/size invalidan la caché si cambia el archivo
    df, info = prepare()
    tm = train_all(df)
    checks = run_checks(df, tm.metrics, tm.selected)
    status, reasons = gate(checks)
    return Context(
        df=df, info=info, tm=tm, p=tm.probs[tm.selected], checks=checks, gate_status=status, gate_reasons=reasons,
        overall=float(df[TARGET].mean()), overall_k=int(df[TARGET].sum()),
        ref_logits=reference_logits(df[df.part == "train"], tm.lr_coef), t_rec=tm.thresholds[tm.selected],
    )


def load_context() -> Context:
    stat = DATA_FILE.stat() if DATA_FILE.exists() else None
    return _build(stat.st_mtime if stat else 0.0, stat.st_size if stat else 0)
