"""Reglas explícitas de intervención para pasajeros con alerta.

Cada regla tiene una condición comprobable con variables del dataset. Se aplica la primera regla que se
cumpla y solo a pasajeros cuya probabilidad supera el umbral de alerta vigente. Ninguna regla usa edad
ni género, para evitar intervenciones basadas únicamente en características personales.
"""
from __future__ import annotations

import pandas as pd

RULES = [
    {
        "id": "R1", "intervencion": "Revisar conexión y ofrecer reacomodo",
        "condicion": "Mal clima pronosticado y vuelo con conexión",
        "test": lambda r: (r["Weather_Issues"] == 1) & (r["Connections"] == 1),
        "porque": "Es la combinación con mayor tasa histórica; el riesgo viene de perder la conexión, no de la intención del pasajero.",
    },
    {
        "id": "R2", "intervencion": "Priorizar asistencia en conexión internacional",
        "condicion": "Vuelo internacional con conexión",
        "test": lambda r: (r["International_Flight"] == 1) & (r["Connections"] == 1),
        "porque": "Las conexiones internacionales concentran tiempos de transbordo y migración.",
    },
    {
        "id": "R3", "intervencion": "Reconfirmar reservación 48 h antes",
        "condicion": "Compra con 2+ semanas de anticipación o Primera clase",
        "test": lambda r: (r["When_Ticket_Purchased"] == 1) | (r["Booking_Class"] == 1),
        "porque": "Son reservas con mayor flexibilidad de cambio; reconfirmar permite liberar el asiento a tiempo.",
    },
    {
        "id": "R4", "intervencion": "Recordatorio por programa de lealtad",
        "condicion": "Viajero frecuente o de negocios",
        "test": lambda r: (r["Frequent_Flier_Status"] == 1) | (r["Business_Traveler"] == 1),
        "porque": "Tienen canal directo (app/lealtad) y suelen cambiar de vuelo en lugar de cancelar.",
    },
    {
        "id": "R5", "intervencion": "Enviar recordatorio y facilitar check-in",
        "condicion": "Cualquier otra alerta",
        "test": lambda r: pd.Series(True, index=r.index),
        "porque": "Intervención de bajo costo para el resto de pasajeros con alerta.",
    },
]

RULE_BY_ID = {r["id"]: r for r in RULES}


def assign(df: pd.DataFrame) -> pd.Series:
    """Devuelve el id de la regla aplicable a cada fila (primera que se cumple)."""
    out = pd.Series("R5", index=df.index)
    assigned = pd.Series(False, index=df.index)
    for r in RULES:
        m = r["test"](df) & ~assigned
        out[m] = r["id"]
        assigned |= m
    return out


def priority(p: pd.Series, threshold: float) -> pd.Series:
    """Alta si la probabilidad es al menos 1.5 veces el umbral (o ≥ 0.6); Media si supera el umbral."""
    hi = max(0.6, min(0.95, threshold * 1.5))
    return pd.Series(pd.NA, index=p.index, dtype=object).mask(p >= threshold, "Media").mask(p >= hi, "Alta")


def rules_table() -> pd.DataFrame:
    return pd.DataFrame([{"Regla": r["id"], "Condición": r["condicion"], "Intervención": r["intervencion"],
                          "Justificación": r["porque"]} for r in RULES])
