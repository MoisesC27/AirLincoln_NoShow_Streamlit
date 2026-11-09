"""Simulación de sobreventa para un tipo de vuelo.

Supuestos (se muestran en la interfaz):
1. El dataset no trae vuelos reales; un "tipo de vuelo" agrupa pasajeros históricos por día, horario,
   salida desde hub y destino.
2. La probabilidad de no-show de un pasajero del tipo de vuelo es la probabilidad media que el modelo
   asigna a los pasajeros históricos de ese grupo (con el escenario de clima elegido).
3. Esa tasa es incierta: se modela con una distribución Beta cuya concentración es el tamaño del grupo (n).
   Así, grupos pequeños producen más incertidumbre. El número de ausentes con B boletos vendidos
   sigue entonces una Beta-binomial.
4. Cada boleto se vende (demanda suficiente) y cada pasajero se presenta o no de forma independiente
   dada la tasa.
Costo esperado(k) = costo_vacío × E[asientos vacíos] + costo_negar × E[pasajeros sin asiento].
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.special import betaln, gammaln


def betabinom_pmf(B: int, a: float, b: float) -> np.ndarray:
    k = np.arange(B + 1)
    log_comb = gammaln(B + 1) - gammaln(k + 1) - gammaln(B - k + 1)
    return np.exp(log_comb + betaln(k + a, B - k + b) - betaln(a, b))


@dataclass
class SimResult:
    curve: pd.DataFrame
    best: pd.Series
    best_unconstrained: pd.Series
    tasa: float
    n: int
    cap: int
    constrained: bool
    feasible: bool


def simulate(rate: float, n_group: int, cap: int, cost_empty: float, cost_deny: float,
             max_extra: int | None = None, max_deny_prob: float | None = None) -> SimResult:
    if not (0 < rate < 1):
        raise ValueError("La tasa prevista debe estar entre 0 y 1.")
    if cap < 1 or n_group < 1:
        raise ValueError("La capacidad y el tamaño del grupo deben ser positivos.")
    a, b = rate * n_group, (1 - rate) * n_group
    if max_extra is None:
        max_extra = int(min(200, max(10, np.ceil(cap * min(0.6, rate * 3 + 0.05)))))
    rows = []
    for k in range(0, max_extra + 1):
        B = cap + k
        pmf = betabinom_pmf(B, a, b)
        N = np.arange(B + 1)  # ausentes
        vac = float((pmf * np.maximum(0, N - k)).sum())
        neg = float((pmf * np.maximum(0, k - N)).sum())
        pneg = float(pmf[N < k].sum())
        rows.append({"extra": k, "boletos": B, "ausentes_esperados": float((pmf * N).sum()),
                     "vacios": vac, "negados": neg, "p_negar": pneg,
                     "costo_vacios": cost_empty * vac, "costo_negar": cost_deny * neg,
                     "costo": cost_empty * vac + cost_deny * neg})
    curve = pd.DataFrame(rows)
    best_unc = curve.loc[curve["costo"].idxmin()]
    best, constrained, feasible = best_unc, False, True
    if max_deny_prob is not None:
        ok = curve[curve["p_negar"] <= max_deny_prob + 1e-12]
        constrained = True
        best = ok.loc[ok["costo"].idxmin()] if len(ok) else curve.iloc[0]
        feasible = len(ok) > 0
    return SimResult(curve, best, best_unc, rate, n_group, cap, constrained, feasible)
