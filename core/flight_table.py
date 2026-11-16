"""Tabla publicada en el tablero: tipos de vuelo con dato, cálculo y simulación separados."""
from __future__ import annotations

import pandas as pd

from .catalog import DAYS, HOURS_SHORT, MIN_N, TARGET
from .overbooking import simulate

# Etiqueta visible de origen para cada columna de la tabla (también va en contrato-datos.md).
ORIGIN = {
    "Día": "dato", "Horario": "dato", "Salida desde hub": "dato", "Destino": "dato",
    "Pasajeros": "calculado", "No-shows": "calculado", "Tasa de no-show": "calculado",
    "Probabilidad prevista": "calculado", "Sobreventa recomendada": "simulado",
    "Costo esperado (MXN)": "simulado", "Diferencia vs. no sobrevender (MXN)": "simulado",
}


def build(df: pd.DataFrame, p: pd.Series, cap: int, cost_empty: float, cost_deny: float) -> pd.DataFrame:
    d = df.assign(p=p)
    g = (d.groupby(["Departure_Day", "Departure_Hour", "Major_Hub_Departure", "International_Flight"])
           .agg(n=(TARGET, "size"), k=(TARGET, "sum"), p=("p", "mean")).reset_index())
    g = g[g.n >= MIN_N]  # política del proyecto: no se publican grupos con menos de 30 pasajeros
    rows = []
    for r in g.itertuples(index=False):
        sim = simulate(float(r.p), int(r.n), cap, cost_empty, cost_deny)
        best, zero = sim.best, sim.curve.iloc[0]
        rows.append({
            "Día": DAYS[r.Departure_Day], "Horario": HOURS_SHORT[r.Departure_Hour],
            "Salida desde hub": "Sí" if r.Major_Hub_Departure else "No",
            "Destino": "Internacional" if r.International_Flight else "Nacional",
            "Pasajeros": int(r.n), "No-shows": int(r.k), "Tasa de no-show": r.k / r.n,
            "Probabilidad prevista": float(r.p), "Sobreventa recomendada": int(best.extra),
            "Costo esperado (MXN)": float(best.costo), "Diferencia vs. no sobrevender (MXN)": float(zero.costo - best.costo),
        })
    return pd.DataFrame(rows).sort_values("Costo esperado (MXN)", ascending=False).reset_index(drop=True)
