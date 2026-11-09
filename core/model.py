"""Entrenamiento, evaluación y explicación de los modelos de clasificación."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, f1_score, roc_auc_score, roc_curve
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from .catalog import FEATURES, RANDOM_STATE, TARGET

LR_NAME = "Regresión logística"
AUC_TIE = 0.01  # diferencias de AUC menores a esto se consideran empate práctico


def _onehot(model):
    return make_pipeline(OneHotEncoder(handle_unknown="ignore"), model)


def model_specs() -> dict:
    return {
        LR_NAME: _onehot(LogisticRegression(max_iter=2000)),
        "Red neuronal": _onehot(MLPClassifier(hidden_layer_sizes=(32,), alpha=1e-2, max_iter=800, random_state=RANDOM_STATE)),
        "Gradient Boosting": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_depth=4, min_samples_leaf=30, random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(n_estimators=400, min_samples_leaf=10, random_state=RANDOM_STATE, n_jobs=-1),
        "Árbol de decisión": DecisionTreeClassifier(max_depth=6, min_samples_leaf=30, random_state=RANDOM_STATE),
    }


def ks_stat(y, p) -> float:
    fpr, tpr, _ = roc_curve(y, p)
    return float(np.max(tpr - fpr))


def best_f1_threshold(y, p) -> float:
    grid = np.round(np.arange(0.05, 0.91, 0.01), 2)
    scores = [f1_score(y, p >= t, zero_division=0) for t in grid]
    return float(grid[int(np.argmax(scores))])


def confusion(y, p, t: float) -> dict:
    y = np.asarray(y).astype(bool)
    yh = np.asarray(p) >= t
    vp = int((yh & y).sum()); fp = int((yh & ~y).sum()); fn = int((~yh & y).sum()); vn = int((~yh & ~y).sum())
    n = vp + fp + fn + vn
    prec = vp / (vp + fp) if vp + fp else 0.0
    rec = vp / (vp + fn) if vp + fn else 0.0
    return {
        "umbral": t, "vp": vp, "fp": fp, "fn": fn, "vn": vn, "n": n,
        "precision": prec, "recall": rec,
        "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
        "alertas": vp + fp, "pct_alertas": (vp + fp) / n if n else 0.0,
        "positivos": vp + fn,
    }


def calibration_bins(y, p, edges=(0, .05, .1, .2, .3, .4, .5, .6, .8, 1.0001)) -> pd.DataFrame:
    df = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    df["bin"] = pd.cut(df["p"], edges, right=False, include_lowest=True)
    g = df.groupby("bin", observed=True).agg(prevista=("p", "mean"), real=("y", "mean"), n=("y", "size")).reset_index()
    g["rango"] = g["bin"].astype(str)
    return g.drop(columns="bin")


def ece(y, p) -> float:
    b = calibration_bins(y, p)
    return float((b["n"] * (b["prevista"] - b["real"]).abs()).sum() / b["n"].sum())


@dataclass
class TrainedModels:
    models: dict
    probs: dict            # nombre -> Serie de probabilidades para todo el df (índice del df)
    thresholds: dict       # nombre -> umbral F1 elegido en validación
    metrics: pd.DataFrame  # filas: modelo × conjunto
    selected: str
    selection_reason: str
    lr_coef: dict          # variable -> {valor: coeficiente}
    lr_intercept: float
    balanced_reference: dict = field(default_factory=dict)


def train_all(df: pd.DataFrame) -> TrainedModels:
    tr = df[df.part == "train"]
    models, probs, thr, rows = {}, {}, {}, []
    for name, m in model_specs().items():
        m.fit(tr[FEATURES], tr[TARGET])
        models[name] = m
        p = pd.Series(m.predict_proba(df[FEATURES])[:, 1], index=df.index)
        probs[name] = p
        va = df.part == "valid"
        thr[name] = best_f1_threshold(df.loc[va, TARGET], p[va])
        for part in ("train", "valid", "test"):
            s = df.part == part
            y, pp = df.loc[s, TARGET], p[s]
            c = confusion(y, pp, thr[name])
            rows.append({
                "modelo": name, "conjunto": part, "n": int(s.sum()), "positivos": int(y.sum()),
                "auc": roc_auc_score(y, pp), "precision": c["precision"], "recall": c["recall"],
                "f1": c["f1"], "ks": ks_stat(y, pp), "brier": brier_score_loss(y, pp), "ece": ece(y, pp),
                "umbral": thr[name],
            })
    metrics = pd.DataFrame(rows)

    # Regla de selección explícita: entre los modelos con AUC de validación a menos de AUC_TIE del mejor,
    # se elige el de menor Brier (mejor calibración), porque el simulador suma probabilidades.
    v = metrics[metrics.conjunto == "valid"].set_index("modelo")
    best_auc = v["auc"].max()
    contenders = v[v["auc"] >= best_auc - AUC_TIE]
    selected = contenders["brier"].idxmin()
    reason = (
        f"Mayor AUC de validación: {v['auc'].idxmax()} ({best_auc:.3f}). Modelos a menos de {AUC_TIE:.2f} de AUC: "
        f"{', '.join(contenders.index)}. Entre ellos se elige el de menor Brier en validación "
        f"({selected}, {v.loc[selected, 'brier']:.4f}) porque el simulador necesita probabilidades bien calibradas."
    )

    lr = models[LR_NAME]
    enc, clf = lr.steps[0][1], lr.steps[1][1]
    coef, i = {}, 0
    for f, cats in zip(FEATURES, enc.categories_):
        coef[f] = {int(c): float(clf.coef_[0][i + j]) for j, c in enumerate(cats)}
        i += len(cats)

    # Referencia: misma regresión con pesos balanceados (planteada en la Entrega 3).
    bal = _onehot(LogisticRegression(max_iter=2000, class_weight="balanced")).fit(tr[FEATURES], tr[TARGET])
    te = df.part == "test"
    pb = bal.predict_proba(df.loc[te, FEATURES])[:, 1]
    balanced = {
        "auc_test": float(roc_auc_score(df.loc[te, TARGET], pb)),
        "prob_media_test": float(pb.mean()),
        "tasa_real_test": float(df.loc[te, TARGET].mean()),
        "ece_test": ece(df.loc[te, TARGET], pb),
    }
    return TrainedModels(models, probs, thr, metrics, selected, reason, coef, float(clf.intercept_[0]), balanced)


def lr_probability(rows: pd.DataFrame, coef: dict, intercept: float) -> np.ndarray:
    z = np.full(len(rows), intercept)
    for f in FEATURES:
        z += rows[f].map(coef[f]).fillna(0).to_numpy()
    return 1 / (1 + np.exp(-z))


def lr_contributions(row: dict, coef: dict, reference: dict) -> pd.DataFrame:
    """Contribución de cada variable en log-odds respecto al pasajero promedio del entrenamiento.

    Para una regresión logística con variables one-hot, logit(p) = b0 + Σ coef[f][x_f]. La diferencia
    coef[f][x_f] − E[coef[f][X_f]] es exacta y suma la diferencia de log-odds frente al promedio.
    """
    out = []
    for f in FEATURES:
        out.append({"variable": f, "valor": row[f], "contribucion": coef[f].get(row[f], 0.0) - reference[f]})
    return pd.DataFrame(out)


def reference_logits(df_train: pd.DataFrame, coef: dict) -> dict:
    return {f: float(df_train[f].map(coef[f]).fillna(0).mean()) for f in FEATURES}


def bootstrap_auc_diff(y, p_a, p_b, n_boot: int = 1000, seed: int = RANDOM_STATE) -> dict:
    """Diferencia AUC(a) − AUC(b) pareada con IC 95% por bootstrap."""
    y = np.asarray(y); p_a = np.asarray(p_a); p_b = np.asarray(p_b)
    rng = np.random.default_rng(seed)
    diffs = []
    n = len(y)
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if y[idx].min() == y[idx].max():
            continue
        diffs.append(roc_auc_score(y[idx], p_a[idx]) - roc_auc_score(y[idx], p_b[idx]))
    diffs = np.array(diffs)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {"diff": float(roc_auc_score(y, p_a) - roc_auc_score(y, p_b)), "lo": float(lo), "hi": float(hi),
            "significativa": bool(lo > 0 or hi < 0)}


def segment_diagnostics(df: pd.DataFrame, p: pd.Series, t: float, part: str = "test") -> pd.DataFrame:
    """Rendimiento del modelo por segmento dentro de un conjunto (por defecto, prueba)."""
    from .catalog import FEATURE_NAMES, VALUE_LABELS
    s = df[df.part == part]
    segs = [("Departure_Hour", None), ("Connections", None), ("Major_Hub_Departure", None),
            ("Booking_Class", None), ("International_Flight", None), ("Weather_Issues", None)]
    rows = []
    for col, _ in segs:
        for val, g in s.groupby(col):
            y = g[TARGET]; pp = p[g.index]
            pos = int(y.sum())
            auc = roc_auc_score(y, pp) if 0 < pos < len(g) else np.nan
            c = confusion(y, pp, t)
            label = VALUE_LABELS.get(col, {}).get(val) or f"{FEATURE_NAMES.get(col, col)}: {'Sí' if val == 1 else 'No'}"
            rows.append({"segmento": label, "variable": FEATURE_NAMES.get(col, col), "n": len(g), "positivos": pos,
                         "auc": auc, "recall": c["recall"] if pos else np.nan, "precision": c["precision"] if c["alertas"] else np.nan})
    out = pd.DataFrame(rows)
    out["confiable"] = (out["n"] >= 30) & (out["positivos"] >= 10)
    return out
