"""Estilos y componentes visuales reutilizables (tema claro con semáforo, como la primera versión)."""
from __future__ import annotations

from html import escape

import streamlit as st

COLORS = {
    "bg": "#F3F5F8", "panel": "#FFFFFF", "soft": "#EEF1F5", "border": "#DDE2EA",
    "text": "#17202C", "muted": "#5D6878", "blue": "#2456A6", "blue_soft": "#E3EBF8",
    "green": "#1D8A4E", "green_soft": "#E1F3E8", "amber": "#B7791F", "amber_soft": "#FBF0DB",
    "red": "#C43D3D", "red_soft": "#F9E2E2", "grey": "#9AA4B2",
}
C = COLORS

STATES = {"ok": "✓", "warn": "!", "bad": "✕"}

CSS = f"""
<style>
[data-testid="stMainBlockContainer"], .block-container {{ padding-top: 3.2rem !important; padding-bottom: 2rem; max-width: 1400px; }}
.al-head h1 {{ font-size:1.55rem; margin:0; padding:0; line-height:1.2; color:{C['text']}; }}
.al-head p {{ margin:2px 0 0; color:{C['muted']}; font-size:0.92rem; }}
.al-strip {{ display:flex; flex-wrap:wrap; gap:8px; margin:8px 0 12px; }}
.al-pill {{ display:inline-flex; align-items:center; gap:6px; padding:3px 12px; border-radius:999px; border:1px solid {C['border']};
 background:{C['panel']}; font-size:0.85rem; color:{C['text']}; }}
.al-pill.ok {{ background:{C['green_soft']}; border-color:{C['green']}; color:{C['green']}; }}
.al-pill.warn {{ background:{C['amber_soft']}; border-color:{C['amber']}; color:{C['amber']}; }}
.al-pill.bad {{ background:{C['red_soft']}; border-color:{C['red']}; color:{C['red']}; }}
.al-kpis {{ display:grid; gap:10px; grid-template-columns:repeat(auto-fit, minmax(min(100%, 175px), 1fr)); margin:6px 0 14px; }}
.al-kpi {{ border-radius:10px; padding:10px 12px; background:{C['soft']}; border-left:5px solid {C['border']}; display:grid; gap:2px; align-content:start; min-width:0; }}
.al-kpi .lbl {{ font-size:0.8rem; color:{C['muted']}; }}
.al-kpi .val {{ font-size:1.6rem; font-weight:650; line-height:1.15; color:{C['text']}; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }}
.al-kpi .st {{ font-size:0.78rem; font-weight:600; }}
.al-kpi .sub {{ font-size:0.76rem; color:{C['muted']}; }}
.al-kpi.s-ok {{ background:{C['green_soft']}; border-left-color:{C['green']}; }} .al-kpi.s-ok .val, .al-kpi.s-ok .st {{ color:{C['green']}; }}
.al-kpi.s-warn {{ background:{C['amber_soft']}; border-left-color:{C['amber']}; }} .al-kpi.s-warn .val, .al-kpi.s-warn .st {{ color:{C['amber']}; }}
.al-kpi.s-bad {{ background:{C['red_soft']}; border-left-color:{C['red']}; }} .al-kpi.s-bad .val, .al-kpi.s-bad .st {{ color:{C['red']}; }}
.al-kpi.lead {{ background:{C['blue_soft']}; border:2px solid {C['blue']}; border-left-width:5px; }}
.al-kpi.lead .val {{ color:{C["blue"]}; font-size:1.75rem; }}
.al-card {{ background:{C['panel']}; border:1px solid {C['border']}; border-radius:12px; padding:12px 16px; margin:4px 0 12px; }}
.al-card h4 {{ margin:0 0 6px; font-size:0.95rem; color:{C['text']}; }}
.al-summary {{ display:grid; gap:6px 20px; grid-template-columns:repeat(auto-fit, minmax(min(100%, 220px), 1fr)); }}
.al-summary .k {{ font-size:0.7rem; text-transform:uppercase; letter-spacing:.06em; color:{C['muted']}; font-weight:700; }}
.al-summary .v {{ font-size:0.9rem; color:{C['text']}; margin-top:1px; }}
.al-close {{ border-left:5px solid {C['blue']}; }}
.al-final {{ display:flex; gap:12px; align-items:center; flex-wrap:wrap; padding:10px 14px; border-radius:10px; border:2px solid {C['green']};
 background:{C['green_soft']}; margin:8px 0; color:{C['green']}; }}
.al-final.bad {{ border-color:{C['red']}; background:{C['red_soft']}; color:{C['red']}; }}
.al-final.warn {{ border-color:{C['amber']}; background:{C['amber_soft']}; color:{C['amber']}; }}
.al-final span {{ color:{C['text']}; font-size:0.85rem; }}
.al-conf {{ display:grid; grid-template-columns:auto 1fr 1fr; gap:6px; font-size:0.85rem; }}
.al-conf div {{ padding:10px 12px; border-radius:8px; border-left:5px solid; }}
.al-conf .h {{ border:none; color:{C['muted']}; font-size:0.78rem; padding:4px 6px; align-self:end; }}
.al-conf .ok {{ background:{C['green_soft']}; border-color:{C['green']}; }}
.al-conf .warn {{ background:{C['amber_soft']}; border-color:{C['amber']}; }}
.al-conf .bad {{ background:{C['red_soft']}; border-color:{C['red']}; }}
.al-conf .n {{ font-size:1.4rem; font-weight:650; display:block; font-variant-numeric:tabular-nums; }}
.al-question {{ font-size:1rem; color:{C['text']}; margin:0 0 4px; }}
.al-legend {{ display:flex; gap:14px; flex-wrap:wrap; font-size:0.8rem; color:{C['muted']}; margin:2px 0 6px; }}
.al-legend span::before {{ content:""; display:inline-block; width:11px; height:11px; border-radius:3px; margin-right:5px; vertical-align:-1px; }}
.al-legend .ok::before {{ background:{C['green']}; }} .al-legend .warn::before {{ background:{C['amber']}; }} .al-legend .bad::before {{ background:{C['red']}; }}
.al-legend .na::before {{ background:{C['grey']}; }}
@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"], .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
  .al-head h1 {{ font-size:1.25rem; }}
  .al-kpi .val {{ font-size:1.35rem; }} .al-kpi.lead .val {{ font-size:1.6rem; }}
}}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def kind(_k: str) -> str:
    """Las etiquetas de tipo de dato se retiraron del diseño; se mantiene la función por compatibilidad."""
    return ""


def kpi_html(label: str, value: str, sub: str = "", k: str | None = None, state: str | None = None,
             state_text: str = "", lead: bool = False) -> str:
    cls = " lead" if lead else (f" s-{state}" if state in STATES else "")
    st_html = f'<span class="st">{STATES[state]} {escape(state_text)}</span>' if state in STATES and state_text else ""
    return (f'<div class="al-kpi{cls}"><div class="lbl">{escape(label)}</div><div class="val">{escape(value)}</div>'
            f'{st_html}<div class="sub">{escape(sub)}</div></div>')


def kpis(items: list[str]) -> None:
    st.markdown('<div class="al-kpis">' + "".join(items) + "</div>", unsafe_allow_html=True)


def legend(items: list[tuple[str, str]]) -> None:
    st.markdown('<div class="al-legend">' + "".join(f'<span class="{c}">{escape(t)}</span>' for c, t in items) + "</div>",
                unsafe_allow_html=True)


def summary(title: str, items: dict[str, str], css: str = "") -> None:
    body = "".join(f'<div><div class="k">{escape(k)}</div><div class="v">{escape(v)}</div></div>' for k, v in items.items())
    st.markdown(f'<div class="al-card {css}"><h4>{escape(title)}</h4><div class="al-summary">{body}</div></div>', unsafe_allow_html=True)


def final_state(text: str, detail: str = "", tone: str = "ok") -> None:
    icon = {"ok": "✓", "warn": "!", "bad": "✕"}[tone]
    st.markdown(f'<div class="al-final {"" if tone == "ok" else tone}"><b>{icon} {escape(text)}</b>'
                f'<span>{escape(detail)}</span></div>', unsafe_allow_html=True)


def ficha(_f: dict) -> None:
    """Las fichas se muestran solo en «Acerca del producto»."""
    return None


def rate_state(t: float) -> tuple[str, str]:
    """Semáforo de tasa de no-show (mismos cortes que el mapa de riesgo)."""
    return ("ok", "Bajo") if t < 0.07 else (("warn", "Medio") if t <= 0.12 else ("bad", "Alto"))


def pct(x: float, d: int = 1) -> str:
    return "—" if x is None or x != x else f"{x * 100:.{d}f}%"


def num(x: float, d: int = 0) -> str:
    return "—" if x is None or x != x else f"{x:,.{d}f}"


def mxn(x: float) -> str:
    return "—" if x is None or x != x else f"${x:,.0f} MXN"
