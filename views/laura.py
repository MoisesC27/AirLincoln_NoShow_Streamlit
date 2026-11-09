"""Laura · Planificación: simulador de sobreventa, mapa de riesgo y propuesta."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from core import security
from core.catalog import DAYS, FEATURES, HOURS, MIN_N, TARGET
from core.content import FICHAS
from core.data import rate_table, wilson
from core.overbooking import betabinom_pmf, simulate
from ui import charts, state
from ui.theme import final_state, kind, kpi_html, kpis, legend, mxn, num, pct, rate_state, summary

CLIMA = {"hist": "Como en el histórico", "alerta": "Mal clima pronosticado", "despejado": "Sin mal clima"}


def _group(ctx, ss) -> tuple[pd.DataFrame, str]:
    df = ctx.df
    m = (df.Departure_Hour == ss.w_l_hora) & (df.Major_Hub_Departure == ss.w_l_hub) & (df.International_Flight == ss.w_l_intl)
    label_day = "todos los días" if ss.w_l_ampliar else DAYS[ss.w_l_dia].lower()
    if not ss.w_l_ampliar:
        m &= df.Departure_Day == ss.w_l_dia
    desc = (f"{label_day}, {HOURS[ss.w_l_hora].lower()}, {'desde hub' if ss.w_l_hub else 'sin hub'}, "
            f"{'internacional' if ss.w_l_intl else 'nacional'}")
    return df[m], desc


def _scenario_prob(ctx, g: pd.DataFrame, clima: str) -> pd.Series:
    if clima == "hist" or g.empty:
        return ctx.p[g.index]
    x = g[FEATURES].copy()
    w = 1 if clima == "alerta" else 0
    x["Weather_Issues"] = w
    x["Weather_Issues___Connection"] = (w & x["Connections"]).astype(int)
    model = ctx.tm.models[ctx.tm.selected]
    return pd.Series(model.predict_proba(x)[:, 1], index=g.index)


@st.cache_data(show_spinner=False)
def _sim_cached(rate, n, cap, cv, cn, tol):
    r = simulate(rate, n, cap, cv, cn, max_deny_prob=tol)
    return r.curve, r.best, r.best_unconstrained, r.feasible


def _interval(rate, n, B, q=(0.1, 0.9)):
    pmf = betabinom_pmf(B, rate * n, (1 - rate) * n)
    cdf = np.cumsum(pmf)
    return int(np.searchsorted(cdf, q[0])), int(np.searchsorted(cdf, q[1]))


def _validate(ss) -> list[str]:
    errs = []
    if not (20 <= ss.w_l_cap <= 600):
        errs.append("Los asientos deben estar entre 20 y 600.")
    if ss.w_l_cv < 0 or ss.w_l_cn < 0:
        errs.append("Los costos no pueden ser negativos.")
    if ss.w_l_cv == 0 and ss.w_l_cn == 0:
        errs.append("Al menos un costo debe ser mayor que cero para comparar estrategias.")
    return errs


def compute(ctx):
    ss = st.session_state
    errs = _validate(ss)
    g, desc = _group(ctx, ss)
    out = {"desc": desc, "n": len(g), "errors": errs, "status": "ok"}
    if errs:
        out["status"] = "error"; return out
    if len(g) == 0:
        out["status"] = "empty"; return out
    k_obs = int(g[TARGET].sum())
    out.update(obs=k_obs / len(g), obs_k=k_obs, ci=wilson(k_obs, len(g)))
    if ss.w_l_base == "historico":
        rate = min(max(k_obs, 0.5), len(g) - 0.5) / len(g)  # evita 0% o 100% exactos
    else:
        rate = float(_scenario_prob(ctx, g, ss.w_l_clima).mean())
    out["rate"] = rate
    if len(g) < MIN_N:
        out["status"] = "insufficient"; return out
    tol = ss.w_l_tol / 100 if ss.w_l_tol_on else None
    curve, best, best_unc, feasible = _sim_cached(round(rate, 6), len(g), int(ss.w_l_cap), float(ss.w_l_cv), float(ss.w_l_cn), tol)
    out.update(curve=curve, best=best, best_unc=best_unc, feasible=feasible, tol=tol)
    if not feasible:
        out["status"] = "inconclusive"
    out["band"] = _interval(rate, len(g), int(best.boletos))
    return out


def _controls(ctx, res):
    ss = st.session_state
    with st.container(border=True):
        st.markdown(f"**A · Características del vuelo** {kind('input')}", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.selectbox("Día", list(DAYS), format_func=DAYS.get, key="w_l_dia", disabled=ss.w_l_ampliar)
        c2.selectbox("Horario", list(HOURS), format_func=HOURS.get, key="w_l_hora")
        c1.radio("Salida desde hub", [1, 0], format_func=lambda v: "Sí" if v else "No", key="w_l_hub", horizontal=True)
        c2.radio("Destino", [0, 1], format_func=lambda v: "Internacional" if v else "Nacional", key="w_l_intl", horizontal=True)
        st.selectbox("Pronóstico del clima", list(CLIMA), format_func=CLIMA.get, key="w_l_clima", disabled=ss.w_l_base == "historico",
                     help="Recalcula la probabilidad de cada pasajero del grupo con el clima indicado.")
        st.toggle("Usar todos los días con este horario", key="w_l_ampliar",
                  help="Amplía el grupo cuando la combinación tiene menos de 30 registros.")
    with st.container(border=True):
        st.markdown(f"**B · Capacidad y costos** {kind('input')}", unsafe_allow_html=True)
        st.number_input("Asientos disponibles", min_value=20, max_value=600, step=1, key="w_l_cap")
        c1, c2 = st.columns(2)
        c1.number_input("Costo de asiento vacío (MXN)", min_value=0, max_value=100_000, step=100, key="w_l_cv",
                        help="Ingreso perdido por un asiento que sale vacío. Supuesto: reemplazar por el dato de la aerolínea.")
        c2.number_input("Costo de negar abordaje (MXN)", min_value=0, max_value=200_000, step=100, key="w_l_cn",
                        help="Compensación, reacomodo y efecto en el cliente por cada pasajero sin asiento. Supuesto.")
    with st.container(border=True):
        st.markdown(f"**C · Parámetros de simulación** {kind('input')}", unsafe_allow_html=True)
        st.radio("Tasa de no-show usada", ["modelo", "historico"], key="w_l_base", horizontal=True,
                 format_func=lambda v: "Predicción del modelo" if v == "modelo" else "Tasa histórica observada",
                 help="El modelo permite escenarios de clima; la tasa histórica usa solo lo ocurrido en el grupo.")
        st.toggle("Limitar la probabilidad de negar abordaje", key="w_l_tol_on")
        st.slider("Tolerancia máxima (%)", 1, 50, key="w_l_tol", disabled=not ss.w_l_tol_on,
                  help="La recomendación busca el menor costo entre las opciones con probabilidad de negar ≤ tolerancia.")
        mx = int(res["curve"].extra.max()) if "curve" in res else 60
        if ss.w_l_manual > mx:
            ss.w_l_manual = mx
        st.slider("Tu alternativa: boletos extra", 0, mx, key="w_l_manual",
                  help="Escenario para comparar contra la recomendación.")
        st.button("Restablecer simulador", on_click=state.reset, args=(state.SIM_KEYS,), use_container_width=True)


def _results(ctx, res, role):
    ss = st.session_state
    st.markdown(f"**{res['desc'].capitalize()}** · {num(res['n'])} pasajeros históricos")
    if res["status"] == "error":
        st.error("**No se puede simular con estos valores.** " + " ".join(res["errors"]))
        st.caption("Corrige los campos marcados o pulsa *Restablecer simulador*.")
        return
    if res["status"] == "empty":
        st.warning("**Sin datos para esta combinación.** No hay pasajeros históricos con este día, horario, hub y destino.")
        st.markdown("**Filtros afectados:** día, horario, hub y destino. **Qué hacer:** activa *Usar todos los días con este horario* "
                    "o cambia el hub o el destino.")
        st.button("Ampliar a todos los días", on_click=lambda: st.session_state.update(w_l_ampliar=True), key="amp_empty")
        return
    obs_txt = f"Observado {pct(res['obs'])} ({res['obs_k']} de {res['n']}; IC 95% {pct(res['ci'][0])}–{pct(res['ci'][1])})"
    if res["status"] == "insufficient":
        st.warning(f"**Datos insuficientes: {res['n']} registros (mínimo {MIN_N}).** El resultado no es concluyente y no se "
                   "emite recomendación.")
        st.markdown(f"Tasa prevista por el modelo: **{pct(res['rate'])}**. {obs_txt}.")
        st.button("Ampliar a todos los días con este horario", on_click=lambda: st.session_state.update(w_l_ampliar=True),
                  type="primary", key="amp_ins")
        return

    curve, best = res["curve"], res["best"]
    k = int(best.extra)
    zero = curve.iloc[0]
    tol = res["tol"]
    if res["status"] == "inconclusive":
        st.warning(f"**Resultado no concluyente:** ninguna sobreventa mantiene la probabilidad de negar abordaje por debajo de "
                   f"{pct(tol, 0)}. Se muestra la opción sin sobreventa. Sube la tolerancia o revisa los costos.")
    pn = float(best.p_negar)
    if tol is not None:
        st_pn = ("ok", "Dentro de tu tolerancia") if pn <= tol else ("bad", "Fuera de tu tolerancia")
    else:
        st_pn = ("ok", "Bajo") if pn < 0.05 else (("warn", "Medio") if pn <= 0.15 else ("bad", "Alto"))
    lo, hi = res["band"]
    diff = float(zero.costo - best.costo)
    rs = rate_state(res["rate"])
    kpis([
        kpi_html("Sobreventa recomendada", f"+{k} boletos", f"vender {num(best.boletos)} para {num(ss.w_l_cap)} asientos", lead=True),
        kpi_html("No-show previsto", pct(res["rate"]), f"real en el histórico: {pct(res['obs'])} ({res['obs_k']} de {res['n']})",
                 state=rs[0], state_text=rs[1]),
        kpi_html("Pasajeros que no llegarán", num(best.ausentes_esperados, 0), f"normalmente entre {lo} y {hi}"),
        kpi_html("Riesgo de negar abordaje", pct(pn), "con la sobreventa recomendada", state=st_pn[0], state_text=st_pn[1]),
        kpi_html("Pasajeros sin asiento", num(best.negados, 1), "promedio por vuelo", state=st_pn[0]),
        kpi_html("Costo esperado", mxn(best.costo), "asientos vacíos + abordajes negados"),
        kpi_html("Menos costo que no sobrevender", mxn(diff), f"sin sobreventa: {mxn(zero.costo)}",
                 state="ok" if diff > 0 else "warn", state_text="Conviene" if diff > 0 else "Sin beneficio"),
    ])
    cut = (tol / 2, tol) if tol else (0.05, 0.15)
    st.markdown("**Costo esperado según los boletos extra**")
    legend([("ok", f"Riesgo de negar abordaje bajo (≤ {pct(cut[0], 0)})"), ("warn", f"Medio (≤ {pct(cut[1], 0)})"), ("bad", "Alto")])
    st.plotly_chart(charts.cost_curve(curve, k, ss.w_l_manual, cut), use_container_width=True, config=charts.CONFIG)
    st.caption(f"El costo más bajo está en +{k}. Antes de ese punto sobran asientos vacíos; después aumentan los pasajeros sin asiento.")


def _map(ctx):
    ss = st.session_state
    df = ctx.df
    f = df
    if ss.w_m_hub != "Todos":
        f = f[f.Major_Hub_Departure == (1 if ss.w_m_hub == "Sí" else 0)]
    if ss.w_m_intl != "Todos":
        f = f[f.International_Flight == (1 if ss.w_m_intl == "Internacional" else 0)]
    left, right = st.columns([3, 2], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("**¿Qué días y horarios tienen más no-show?**")
            c1, c2, c3 = st.columns([1, 1, 1])
            c1.selectbox("Salida desde hub", ["Todos", "Sí", "No"], key="w_m_hub")
            c2.selectbox("Destino", ["Todos", "Nacional", "Internacional"], key="w_m_intl")
            c3.button("Quitar filtros", on_click=state.reset, args=(state.MAP_KEYS,), use_container_width=True)
            st.caption(f"{len(f):,} de {len(df):,} pasajeros")
            if f.empty:
                st.warning("Sin datos con estos filtros. Pulsa *Quitar filtros*.")
                return
            grid = rate_table(f, ["Departure_Day", "Departure_Hour"])
            full = pd.MultiIndex.from_product([range(1, 8), range(1, 4)], names=["Departure_Day", "Departure_Hour"]).to_frame(index=False)
            grid = full.merge(grid, how="left").fillna({"registros": 0, "ausencias": 0}).astype({"registros": int, "ausencias": int})
            grid = security.complementary_suppression(security.suppress(grid), row="Departure_Hour")
            legend([("ok", "Menos de 7%"), ("warn", "7% a 12%"), ("bad", "Más de 12%"), ("na", "Menos de 30 pasajeros")])
            st.plotly_chart(charts.heatmap(grid, float(f[TARGET].mean())), use_container_width=True, config=charts.CONFIG)
    with right:
        with st.container(border=True):
            st.markdown("**Combinaciones con mayor no-show**")
            top = rate_table(f, ["Departure_Day", "Departure_Hour", "Major_Hub_Departure", "International_Flight"])
            top = top[top.registros >= MIN_N].sort_values("tasa", ascending=False).head(6)
            for i, o in enumerate(top.itertuples(index=False)):
                c = rate_state(o.tasa)[0]
                color = {"ok": "#1D8A4E", "warn": "#B7791F", "bad": "#C43D3D"}[c]
                a, b = st.columns([4, 1.4], vertical_alignment="center")
                a.markdown(f"**{DAYS[o.Departure_Day]} · {HOURS[o.Departure_Hour].split(' ')[0]}** "
                           f"<span style='color:{color};font-weight:700'>{o.tasa * 100:.0f}%</span><br>"
                           f"<span style='font-size:0.8rem;color:#5D6878'>{'Desde hub' if o.Major_Hub_Departure else 'Sin hub'} · "
                           f"{'Internacional' if o.International_Flight else 'Nacional'} · {o.ausencias} de {o.registros}</span>",
                           unsafe_allow_html=True)
                b.button("Simular", key=f"sim_{i}", use_container_width=True, on_click=lambda o=o: st.session_state.update(
                    w_l_dia=int(o.Departure_Day), w_l_hora=int(o.Departure_Hour), w_l_hub=int(o.Major_Hub_Departure),
                    w_l_intl=int(o.International_Flight), w_l_ampliar=False, _goto_sim=True))
            if st.session_state.pop("_goto_sim", False):
                st.success("Cargado en **Simulador de sobreventa**.")


def _close(ctx, res, role):
    ss = st.session_state
    if res["status"] not in ("ok", "inconclusive"):
        summary("Cierre", {"Estado": "Sin propuesta: el simulador no tiene un resultado concluyente.",
                           "Siguiente acción": "Vuelve al simulador y resuelve el aviso mostrado."}, "al-close")
        return
    b, zero, k = res["best"], res["curve"].iloc[0], int(res["best"].extra)
    items = {
        "Hallazgo principal": f"Para {res['desc']}, el modelo prevé {pct(res['rate'])} de no-show (≈{num(res['rate'] * ss.w_l_cap, 0)} asientos libres sin sobreventa).",
        "Decisión recomendada": f"Vender {num(b.boletos)} boletos para {num(ss.w_l_cap)} asientos (+{k}).",
        "Evidencia": f"Costo esperado {mxn(b.costo)} frente a {mxn(zero.costo)} sin sobreventa; {num(res['n'])} pasajeros históricos.",
        "Riesgos y limitaciones": f"Prob. de negar ≥1 abordaje {pct(b.p_negar)}; simulación sin vuelos reales; costos supuestos.",
        "Siguiente acción": "Validar costos reales con Finanzas y probar la política en un grupo piloto de vuelos.",
    }
    summary("Cierre · Propuesta de sobreventa", items, "al-close")
    sig = (res["desc"], k, int(ss.w_l_cap), int(ss.w_l_cv), int(ss.w_l_cn), ss.w_l_clima)
    if st.button("Preparar propuesta", type="primary"):
        ss["l_propuesta"] = {"sig": sig, **items}
    prop = ss.get("l_propuesta")
    if prop and prop["sig"] == sig:
        final_state("Propuesta de sobreventa preparada", prop["Decisión recomendada"])
        if security.can(role, "exportar_agregados"):
            txt = "\n".join(f"{k_}: {v}" for k_, v in prop.items() if k_ != "sig")
            st.download_button("Descargar propuesta (datos agregados)", txt, "propuesta_sobreventa.txt")
        else:
            st.caption("La descarga de propuestas requiere iniciar sesión con un rol autorizado.")
    elif prop:
        st.info("Cambiaste parámetros después de preparar la propuesta. Prepárala de nuevo para que coincida con el escenario actual.")


def render(ctx, role):
    res = compute(ctx)
    if res["status"] in ("ok", "inconclusive"):
        b = res["best"]
        summary("Resumen ejecutivo", {
            "Hallazgo": f"{res['desc'].capitalize()}: no-show previsto {pct(res['rate'])} (observado {pct(res['obs'])}, n = {num(res['n'])}).",
            "Indicador de respaldo": f"Costo esperado mínimo {mxn(b.costo)} con +{int(b.extra)} boletos.",
            "Recomendación": f"Vender {num(b.boletos)} boletos para {num(st.session_state.w_l_cap)} asientos.",
            "Limitación": "Simulación de escenario: el dataset no identifica vuelos ni demanda real.",
        })
    else:
        summary("Resumen ejecutivo", {"Estado": {"error": "Valores inválidos en el simulador.", "empty": "Sin datos para la combinación elegida.",
                                                 "insufficient": f"Datos insuficientes ({res['n']} registros, mínimo {MIN_N})."}[res["status"]],
                                      "Siguiente acción": "Ajusta la combinación o amplía el grupo."})
    t1, t2, t3 = st.tabs(["Simulador de sobreventa", "Mapa de riesgo histórico", "Propuesta y cierre"])
    with t1:
        left, right = st.columns([1, 2], gap="large")
        with left:
            _controls(ctx, res)
        with right:
            with st.spinner("Calculando escenario…"):
                _results(ctx, res, role)
    with t2:
        _map(ctx)
    with t3:
        _close(ctx, res, role)
