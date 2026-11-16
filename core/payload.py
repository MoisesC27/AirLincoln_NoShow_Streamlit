"""Construye los datos que consume la plantilla visual del dashboard, a partir del CSV real y los modelos entrenados."""
from __future__ import annotations

import numpy as np

from .catalog import FEATURES, ID_COL, TARGET
from .model import LR_NAME, calibration_bins, confusion
from .quality import psi_table

PART_CODE = {"train": 0, "valid": 1, "test": 2}


def build_payload(ctx, start: str | None = None, lock: bool = False, threshold: float | None = None) -> dict:
    df, tm = ctx.df, ctx.tm
    p_lr = tm.probs[LR_NAME]  # la plantilla recalcula probabilidades con los coeficientes de la regresión logística

    cols = [ID_COL, TARGET, "Major_Hub_Departure"] + FEATURES
    rows = df[cols].astype(int).values.tolist()
    for r, part in zip(rows, df["part"]):
        r.append(PART_CODE[part])
    # Fecha y vuelo de cada pasajero (columnas opcionales): índices a las listas «fechas» y «vuelos».
    vuelos = list(getattr(ctx, "vuelos", []) or [])
    fechas = sorted(df["Flight_Date"].dropna().unique().tolist()) if "Flight_Date" in df.columns else []
    fi = {f: i for i, f in enumerate(fechas)}
    vi = {v[0]: i for i, v in enumerate(vuelos)}
    fd = df["Flight_Date"] if "Flight_Date" in df.columns else [None] * len(df)
    fn = df["Flight_Number"] if "Flight_Number" in df.columns else [None] * len(df)
    for r, d, n in zip(rows, fd, fn):
        r.append(fi.get(d, -1))
        r.append(vi.get(n, -1))

    m = tm.metrics.set_index(["modelo", "conjunto"])
    models = [{"m": name, "auc": round(float(m.loc[(name, "test"), "auc"]), 3), "aucv": round(float(m.loc[(name, "valid"), "auc"]), 3),
               "rec": round(float(m.loc[(name, "test"), "recall"]), 3), "prec": round(float(m.loc[(name, "test"), "precision"]), 3)}
              for name in tm.models]

    ev = df["part"] != "train"
    y, p = df.loc[ev, TARGET], p_lr[ev]
    curve = []
    for t in np.round(np.arange(0.05, 0.91, 0.01), 2):
        c = confusion(y, p, float(t))
        curve.append([float(t), c["vp"], c["fp"], c["fn"], c["vn"]])

    cal = calibration_bins(y, p)
    ps = psi_table(df)

    return {
        "vuelos": vuelos,
        "vuelos_prob": list(getattr(ctx, "vuelos_prob", []) or []),
        "fechas": fechas,
        "b0": round(tm.lr_intercept, 6),
        "coef": {f: {str(k): round(v, 6) for k, v in tm.lr_coef[f].items()} for f in FEATURES},
        "thr": round(float(threshold if threshold is not None else tm.thresholds[LR_NAME]), 2),
        "thr_rec": round(float(tm.thresholds[LR_NAME]), 2),
        "rows": rows,
        "models": models,
        "curve": curve,
        "cal": [[round(float(a), 4), round(float(b), 4), int(n)] for a, b, n in zip(cal.prevista, cal.real, cal.n)],
        "psi": {r.variable: round(float(r.psi), 4) for r in ps.itertuples()},
        "dq": {"rows": int(len(df)), "uniq_ids": int(df[ID_COL].nunique()),
               "invalid": int(df.attrs.get("invalid_rows", 0)), "excluded": int(df.attrs.get("excluded_rows", 0)),
               "problems": list(df.attrs.get("problems", []))},
        "start": start,
        "lock": bool(lock and start),
    }
