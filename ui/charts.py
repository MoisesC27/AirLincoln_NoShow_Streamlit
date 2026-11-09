"""Gráficas Plotly con el estilo claro del producto. Cada función recibe datos ya calculados."""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.catalog import DAYS_SHORT, HOURS_SHORT
from .theme import COLORS as C

CONFIG = {"displaylogo": False, "responsive": True, "displayModeBar": False}
GRID = "#E6EAF0"


def _base(fig: go.Figure, height: int = 340, **kw) -> go.Figure:
    fig.update_layout(
        height=height, template="plotly_white", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=C["text"], size=13), margin=dict(l=8, r=8, t=30, b=8),
        hoverlabel=dict(bgcolor="white", bordercolor=C["border"], font_color=C["text"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, bgcolor="rgba(0,0,0,0)"), **kw)
    fig.update_xaxes(gridcolor=GRID, zerolinecolor="#C9D1DC", automargin=True)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor="#C9D1DC", automargin=True)
    return fig


def cost_curve(curve: pd.DataFrame, best_k: int, manual_k: int | None, risk_cut: tuple[float, float]) -> go.Figure:
    low, high = risk_cut
    fig = go.Figure()
    zone = np.where(curve.p_negar <= low, "ok", np.where(curve.p_negar <= high, "warn", "bad"))
    fill = {"ok": C["green_soft"], "warn": C["amber_soft"], "bad": C["red_soft"]}
    start = 0
    for i in range(1, len(curve) + 1):
        if i == len(curve) or zone[i] != zone[start]:
            fig.add_vrect(x0=curve.extra.iloc[start] - 0.5, x1=curve.extra.iloc[i - 1] + 0.5, fillcolor=fill[zone[start]],
                          opacity=1, line_width=0, layer="below")
            start = i
    fig.add_trace(go.Scatter(
        x=curve.extra, y=curve.costo, mode="lines", name="Costo esperado", line=dict(color=C["blue"], width=3),
        customdata=np.c_[curve.boletos, curve.vacios, curve.negados, curve.p_negar * 100],
        hovertemplate="<b>+%{x} boletos</b> (%{customdata[0]:.0f} vendidos)<br>Costo esperado: $%{y:,.0f} MXN"
                      "<br>Asientos vacíos: %{customdata[1]:.1f}<br>Pasajeros sin asiento: %{customdata[2]:.2f}"
                      "<br>Riesgo de negar abordaje: %{customdata[3]:.1f}%<extra></extra>"))
    b = curve[curve.extra == best_k].iloc[0]
    fig.add_trace(go.Scatter(x=[best_k], y=[b.costo], mode="markers", name=f"Recomendada (+{best_k})",
                             marker=dict(size=13, color=C["blue"], line=dict(color="white", width=2)), hoverinfo="skip"))
    if manual_k is not None and manual_k != best_k and manual_k in set(curve.extra):
        m = curve[curve.extra == manual_k].iloc[0]
        fig.add_trace(go.Scatter(x=[manual_k], y=[m.costo], mode="markers", name=f"Tu alternativa (+{manual_k})",
                                 marker=dict(size=12, symbol="diamond", color=C["amber"]), hoverinfo="skip"))
    _base(fig, 330)
    fig.update_xaxes(title="Boletos extra sobre la capacidad")
    fig.update_yaxes(title="Costo esperado (MXN)", tickprefix="$", tickformat="~s", rangemode="tozero")
    return fig


def rate_color(t: float) -> str:
    return "ok" if t < 0.07 else ("warn" if t <= 0.12 else "bad")


def heatmap(grid: pd.DataFrame, overall: float) -> go.Figure:
    """Mapa día × horario con colores de semáforo (verde < 7%, ámbar 7–12%, rojo > 12%), como la primera versión."""
    fig = go.Figure()
    for r in grid.itertuples():
        x, y = r.Departure_Day, r.Departure_Hour
        if r.suprimido:
            fc, lc, txt, tc = C["soft"], C["grey"], "n<30", C["muted"]
            hover = f"{DAYS_SHORT[x]} · {HOURS_SHORT[y]}<br>" + ("Menos de 30 registros" if not r.complementaria else "Oculto para proteger un grupo pequeño")
        else:
            c = rate_color(r.tasa)
            fc, lc, tc = C[{"ok": "green_soft", "warn": "amber_soft", "bad": "red_soft"}[c]], C[{"ok": "green", "warn": "amber", "bad": "red"}[c]], None
            tc = lc
            txt = f"{r.tasa * 100:.0f}%"
            hover = (f"<b>{DAYS_SHORT[x]} · {HOURS_SHORT[y]}</b><br>{r.tasa * 100:.1f}% no se presentó"
                     f"<br>{int(r.ausencias):,} de {int(r.registros):,} pasajeros")
        fig.add_shape(type="rect", x0=x - 0.46, x1=x + 0.46, y0=y - 0.44, y1=y + 0.44, fillcolor=fc,
                      line=dict(color=lc, width=1.5), layer="below")
        fig.add_trace(go.Scatter(x=[x], y=[y], mode="text", text=[f"<b>{txt}</b>"], textfont=dict(size=16, color=tc),
                                 hovertemplate=hover + "<extra></extra>", showlegend=False))
        fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers", marker=dict(size=40, opacity=0), hovertemplate=hover + "<extra></extra>",
                                 showlegend=False))
    _base(fig, 290, showlegend=False)
    fig.update_xaxes(tickvals=list(range(1, 8)), ticktext=[DAYS_SHORT[d] for d in range(1, 8)], side="top", showgrid=False,
                     zeroline=False, range=[0.5, 7.5], fixedrange=True)
    fig.update_yaxes(tickvals=[1, 2, 3], ticktext=[HOURS_SHORT[h] for h in range(1, 4)], showgrid=False, zeroline=False,
                     range=[3.5, 0.5], fixedrange=True)
    return fig


def segment_bars(t: pd.DataFrame, overall: float) -> go.Figure:
    t = t.sort_values("tasa")
    cls = [rate_color(v) if v > overall or True else "ok" for v in t.tasa]
    cls = ["ok" if v < overall else ("warn" if v <= 2 * overall else "bad") for v in t.tasa]
    colors = [C[{"ok": "green", "warn": "amber", "bad": "red"}[c]] for c in cls]
    fig = go.Figure(go.Bar(
        x=t.tasa * 100, y=t.segmento, orientation="h", marker_color=colors,
        text=[f"{r * 100:.0f}%" for r in t.tasa], textposition="outside", cliponaxis=False,
        customdata=np.c_[t.ausencias, t.registros, t.tasa / overall],
        hovertemplate="<b>%{y}</b><br>%{x:.1f}% no se presentó (%{customdata[0]:,} de %{customdata[1]:,})"
                      "<br>%{customdata[2]:.1f} veces el promedio<extra></extra>"))
    fig.add_vline(x=overall * 100, line=dict(color=C["text"], dash="dash", width=1),
                  annotation_text=f"Promedio {overall * 100:.0f}%", annotation_position="top", annotation_font_color=C["muted"])
    _base(fig, max(300, 28 * len(t) + 50), showlegend=False)
    fig.update_xaxes(title="% de no-show", ticksuffix="%", range=[0, min(100, t.tasa.max() * 100 * 1.15)])
    return fig


def importance_bars(imp: pd.DataFrame) -> go.Figure:
    imp = imp.sort_values("rango")
    fig = go.Figure(go.Bar(x=imp.rango, y=imp.nombre, orientation="h", marker_color=C["blue"],
                           text=[f"{v:.2f}" for v in imp.rango], textposition="outside", cliponaxis=False,
                           hovertemplate="<b>%{y}</b><br>Peso en el modelo: %{x:.2f}<extra></extra>"))
    _base(fig, max(280, 28 * len(imp) + 50), showlegend=False)
    fig.update_xaxes(title="Peso en el modelo", range=[0, imp.rango.max() * 1.2])
    return fig


def contrib_bars(c: pd.DataFrame) -> go.Figure:
    c = c.sort_values("contribucion")
    fig = go.Figure(go.Bar(
        x=c.contribucion, y=c.etiqueta, orientation="h",
        marker_color=[C["red"] if v > 0 else C["green"] for v in c.contribucion],
        text=["▲ sube" if v > 0 else "▼ baja" for v in c.contribucion], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>%{x:+.2f} frente al pasajero promedio<extra></extra>"))
    ext = max(0.5, c.contribucion.abs().max() * 1.4)
    _base(fig, max(260, 30 * len(c) + 50), showlegend=False)
    fig.update_xaxes(title="Efecto en el riesgo", range=[-ext, ext], zeroline=True, showticklabels=False)
    return fig


def auc_dots(df: pd.DataFrame) -> go.Figure:
    df = df.sort_values("auc")
    fig = go.Figure(go.Bar(
        x=df.auc, y=df.modelo, orientation="h", marker_color=[C["green"] if s else "#C9D1DC" for s in df.seleccionado],
        text=[f"{a:.3f}" for a in df.auc], textposition="outside", cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>AUC prueba: %{x:.3f}<extra></extra>"))
    _base(fig, 260, showlegend=False)
    fig.update_xaxes(title="AUC en prueba (1 = perfecto, 0.5 = azar)", range=[0.5, 1.0])
    return fig


def calibration(b: pd.DataFrame) -> go.Figure:
    b = b[b.n >= 20].reset_index(drop=True)
    labels = [f"{p * 100:.0f}%" for p in b.prevista]
    ok = (b.prevista - b.real).abs() <= 0.05
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=b.prevista, name="Lo que dijo el modelo", marker_color="#C9D1DC",
                         hovertemplate="Previsto %{y:.1%}<extra></extra>"))
    fig.add_trace(go.Bar(x=labels, y=b.real, name="Lo que pasó", marker_color=[C["green"] if o else C["amber"] for o in ok],
                         customdata=b.n, hovertemplate="Real %{y:.1%} · n = %{customdata:,}<extra></extra>"))
    _base(fig, 300, barmode="group")
    fig.update_xaxes(title="Grupos por probabilidad prevista")
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    return fig


def threshold_tradeoff(rows: pd.DataFrame, t: float, t_rec: float) -> go.Figure:
    fig = go.Figure()
    for col, name, color in (("recall", "No-shows detectados", C["green"]), ("precision", "Alertas correctas", C["blue"]),
                             ("pct_alertas", "% de pasajeros con alerta", C["amber"])):
        fig.add_trace(go.Scatter(x=rows.umbral, y=rows[col], name=name, mode="lines", line=dict(color=color, width=2.5),
                                 hovertemplate=f"{name}: %{{y:.1%}}<br>Umbral %{{x:.2f}}<extra></extra>"))
    fig.add_vline(x=t, line=dict(color=C["text"], width=2), annotation_text=f"Elegido {t:.2f}", annotation_position="top right")
    if abs(t - t_rec) > 1e-9:
        fig.add_vline(x=t_rec, line=dict(color=C["muted"], width=1, dash="dot"))
    _base(fig, 300)
    fig.update_xaxes(title="Umbral de alerta", range=[0.05, 0.9])
    fig.update_yaxes(tickformat=".0%", range=[0, 1.02])
    return fig
