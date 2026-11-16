"""Contexto compartido: datos, modelos y validaciones, calculados una vez y guardados en caché."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from . import flights
from .catalog import TARGET
from .data import DATA_FILE, DatasetInfo, prepare_bytes
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
    vuelos: list
    vuelos_prob: list


@st.cache_resource(show_spinner="Validando el archivo y entrenando los 5 modelos…", max_entries=3)
def build_context(data: bytes, name: str) -> Context:
    """Un contexto por archivo: si cambia el contenido, se recalcula todo con los datos nuevos."""
    df, info = prepare_bytes(data, name)
    tm = train_all(df)
    checks = run_checks(df, tm.metrics, tm.selected)
    status, reasons = gate(checks)
    vl, vp = flights.load_bytes(data, name)
    return Context(
        df=df, info=info, tm=tm, p=tm.probs[tm.selected], checks=checks, gate_status=status, gate_reasons=reasons,
        overall=float(df[TARGET].mean()), overall_k=int(df[TARGET].sum()),
        ref_logits=reference_logits(df[df.part == "train"], tm.lr_coef), t_rec=tm.thresholds[tm.selected], vuelos=vl, vuelos_prob=vp,
    )


def load_context() -> Context:
    """Archivo de ejemplo incluido en el proyecto (data/AIRLINCOLNDATA2.csv)."""
    return build_context(DATA_FILE.read_bytes(), DATA_FILE.name)
