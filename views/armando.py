"""Armando · Experiencia del pasajero: segmentos, intervenciones, predicción individual y cierre."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from core import interventions as iv
from core import security
from core.catalog import (AGES, CLASSES, DAYS, FEATURE_NAMES, FEATURES, HOURS, MIN_N, PURCHASE, TARGET, VALUE_LABELS)
from core.content import FICHAS
from core.data import rate_table
from core.model import lr_contributions, lr_probability
from ui import charts
from ui.theme import final_state, ficha, kind, kpi_html, kpis, legend, num, pct, rate_state, summary

SEGMENTS = [
    ("Primera clase", lambda d: d.Booking_Class == 1), ("Clase Business", lambda d: d.Booking_Class == 2),
    ("Clase Coach", lambda d: d.Booking_Class == 3),
    ("Compra 2+ semanas antes", lambda d: d.When_Ticket_Purchased == 1),
    ("Compra < 2 semanas antes", lambda d: d.When_Ticket_Purchased == 2),
    ("Compra el mismo día", lambda d: d.When_Ticket_Purchased == 3),
    ("Viajero frecuente", lambda d: d.Frequent_Flier_Status == 1), ("Viaja por negocios", lambda d: d.Business_Traveler == 1),
    ("Con conexión", lambda d: d.Connections == 1), ("Vuelo internacional", lambda d: d.International_Flight == 1),
    ("Mal clima", lambda d: d.Weather_Issues == 1), ("Mal clima + conexión", lambda d: d.Weather_Issues___Connection == 1),
    ("Sale en la mañana", lambda d: d.Departure_Hour == 1), ("Sale en la tarde", lambda d: d.Departure_Hour == 2),
    ("Sale de noche", lambda d: d.Departure_Hour == 3), ("Salida desde hub", lambda d: d.Major_Hub_Departure == 1),
]


@st.cache_data(show_spinner=False)
def segment_table(_df: pd.DataFrame, key: str) -> pd.DataFrame:
    rows = []
    for name, f in SEGMENTS:
        s = _df[f(_df)]
        t = rate_table(s.assign(seg=name), ["seg"])
        rows.append(t.rename(columns={"seg": "segmento"}))
    return pd.concat(rows, ignore_index=True)


def _threshold(ctx) -> float:
    return float(st.session_state.get("w_umbral") or ctx.t_rec)


def _portfolio(ctx, t: float) -> pd.DataFrame:
    """Pasajeros no usados para entrenar (validación + prueba) con su alerta, regla y prioridad."""
    d = ctx.df[ctx.df.part != "train"].copy()
    d["p"] = ctx.p[d.index]
    d["alerta"] = d.p >= t
    d["regla"] = iv.assign(d)
    d["prioridad"] = iv.priority(d.p, t)
    return d


def _segments(ctx):
    t = segment_table(ctx.df, ctx.info.sha256)
    t = security.suppress(t)
    pub = t[~t.suprimido]
    hidden = t[t.suprimido]
    above = pub[pub.ic_bajo > ctx.overall].sort_values("tasa", ascending=False)
    st.markdown(f"**Tasa de no-show observada por segmento** {kind('hist')}", unsafe_allow_html=True)
    legend([("ok", "Menos que el promedio"), ("warn", "Hasta 2 veces el promedio"), ("bad", "Más de 2 veces el promedio")])
    st.plotly_chart(charts.segment_bars(pub, ctx.overall), use_container_width=True, config=charts.CONFIG)
    if len(above):
        top = above.iloc[0]
        st.markdown(f"**Lectura:** {len(above)} segmentos están por encima del promedio ({pct(ctx.overall)}) con evidencia suficiente. "
                    f"El mayor es **{top.segmento}**: {pct(top.tasa)} ({int(top.ausencias):,} de {int(top.registros):,}), "
                    f"{(top.tasa - ctx.overall) * 100:+.1f} puntos frente al promedio. Es una asociación histórica, no una causa demostrada.")
    if len(hidden):
        st.caption("Ocultos por tener menos de 30 registros: " + ", ".join(hidden.segmento))
    ficha(FICHAS["segmentos"])

    st.markdown(f"#### Peso de cada variable en el modelo {kind('pred')}", unsafe_allow_html=True)
    st.caption("Cuánto usa el modelo cada variable para calcular el riesgo (distinto de la tasa histórica de arriba).")
    imp = pd.DataFrame([{"nombre": FEATURE_NAMES[f], "rango": max(c.values()) - min(c.values())} for f, c in ctx.tm.lr_coef.items()])
    st.plotly_chart(charts.importance_bars(imp), use_container_width=True, config=charts.CONFIG)
    ficha(FICHAS["importancia"])


def _demo_passengers(ctx, t: float) -> pd.DataFrame:
    """Pasajeros FICTICIOS generados al azar (semilla fija) para demostrar la vista restringida."""
    rng = np.random.default_rng(7)
    n = 400
    d = pd.DataFrame({
        "Age": rng.integers(1, 9, n), "Booking_Class": rng.choice([1, 2, 3], n, p=[.05, .2, .75]),
        "Business_Traveler": rng.binomial(1, .3, n), "Connections": rng.binomial(1, .3, n),
        "Departure_Day": rng.integers(1, 8, n), "Departure_Hour": rng.integers(1, 4, n),
        "Frequent_Flier_Status": rng.binomial(1, .1, n), "International_Flight": rng.binomial(1, .1, n),
        "When_Ticket_Purchased": rng.choice([1, 2, 3], n, p=[.1, .5, .4]), "Weather_Issues": rng.binomial(1, .15, n),
    })
    d["Weather_Issues___Connection"] = d.Weather_Issues & d.Connections
    d["p"] = lr_probability(d, ctx.tm.lr_coef, ctx.tm.lr_intercept)
    d["regla"] = iv.assign(d); d["prioridad"] = iv.priority(d.p, t)
    d = d[d.p >= t].sort_values("p", ascending=False).head(12)
    d["id"] = [f"FICTICIO-{i:03d}" for i in range(1, len(d) + 1)]
    return d


def _main_factor(ctx, row) -> str:
    c = lr_contributions(row, ctx.tm.lr_coef, ctx.ref_logits)
    c = c[c.variable != "Weather_Issues___Connection"].sort_values("contribucion", ascending=False).iloc[0]
    return VALUE_LABELS[c.variable][int(c.valor)]


def _priority_table(ctx, d: pd.DataFrame, id_fn) -> pd.DataFrame:
    rows = []
    for r in d.itertuples():
        row = {f: int(getattr(r, f)) for f in FEATURES}
        rows.append({"Pasajero": id_fn(r), "Probabilidad": pct(r.p), "Riesgo": "Alto" if r.prioridad == "Alta" else "Medio",
                     "Factor principal": _main_factor(ctx, row), "Acción propuesta": iv.RULE_BY_ID[r.regla]["intervencion"],
                     "Prioridad": f"{'▲▲' if r.prioridad == 'Alta' else '▲'} {r.prioridad}"})
    return pd.DataFrame(rows)


def _interventions(ctx, role):
    ss = st.session_state
    t = _threshold(ctx)
    d = _portfolio(ctx, t)
    al = d[d.alerta]
    st.caption(f"Cartera: {len(d):,} pasajeros no usados para entrenar (validación + prueba). Umbral de alerta vigente: "
               f"{t:.2f} (lo ajusta Anna; recomendado {ctx.t_rec:.2f}). Pasajeros con alerta: {len(al):,} ({pct(len(al) / len(d))}).")
    st.markdown("**Reglas de asignación** (se aplica la primera que se cumple; ninguna usa edad ni género)")
    st.table(iv.rules_table().set_index("Regla"))

    agg = []
    for r in iv.RULES:
        g = al[al.regla == r["id"]]
        agg.append({"id": r["id"], "intervencion": r["intervencion"], "n": len(g), "alta": int((g.prioridad == "Alta").sum()),
                    "esperados": float(g.p.sum()), "real": int(g[TARGET].sum())})
    agg = pd.DataFrame(agg)
    view = pd.DataFrame({
        "Regla": agg.id, "Intervención": agg.intervencion,
        "Pasajeros con alerta": np.where(agg.n < MIN_N, "< 30", agg.n.map("{:,}".format)),
        "Prioridad alta": np.where(agg.n < MIN_N, "—", agg.alta.map("{:,}".format)),
        "No-shows esperados (modelo)": np.where(agg.n < MIN_N, "—", agg.esperados.map("{:,.1f}".format)),
        "No-shows ocurridos (histórico)": np.where(agg.n < MIN_N, "—", agg.real.map("{:,}".format)),
    })
    st.markdown(f"**Pasajeros con alerta por intervención** {kind('pred')} {kind('hist')}", unsafe_allow_html=True)
    st.dataframe(view, hide_index=True, use_container_width=True)
    st.caption("Grupos con menos de 30 pasajeros se suprimen. «Esperados» suma las probabilidades del modelo; «ocurridos» es el resultado real.")

    st.markdown("#### Preparar una intervención")
    rid = st.selectbox("Segmento a priorizar", [r["id"] for r in iv.RULES], key="w_a_rule",
                       format_func=lambda i: f"{i} · {iv.RULE_BY_ID[i]['intervencion']}")
    rule = iv.RULE_BY_ID[rid]
    row = agg.set_index("id").loc[rid]
    if row.n == 0:
        st.warning("**Sin pasajeros con alerta en este segmento** con el umbral actual. Elige otro segmento o pide a Anna revisar el umbral.")
    elif row.n < MIN_N:
        st.warning(f"**Segmento pequeño (< {MIN_N} pasajeros con alerta).** Los resultados no se publican; elige otro segmento.")
    else:
        kpis([
            kpi_html("Pasajeros con alerta", num(row.n), rule["condicion"], "pred", lead=True),
            kpi_html("Prioridad alta", num(row.alta), "probabilidad ≥ 1.5 × umbral (mín. 0.6)", "deriv"),
            kpi_html("No-shows esperados", num(row.esperados, 1), "suma de probabilidades", "pred"),
            kpi_html("Alertas acertadas (histórico)", pct(row.real / row.n), f"{row.real:,} de {row.n:,} con alerta faltaron", "hist",
                     "ok" if row.real / row.n >= 0.55 else ("warn" if row.real / row.n >= 0.35 else "bad"),
                     "Buena" if row.real / row.n >= 0.55 else ("Media" if row.real / row.n >= 0.35 else "Baja")),
        ])
        st.markdown(f"**Por qué:** {rule['porque']}")
        if st.button("Preparar intervención", type="primary"):
            ss["a_interv"] = {"rid": rid, "t": t, "n": int(row.n), "alta": int(row.alta), "esp": float(row.esperados)}
        prep = ss.get("a_interv")
        if prep and prep["rid"] == rid and abs(prep["t"] - t) < 1e-9:
            final_state("Segmento priorizado e intervención preparada",
                        f"{rule['intervencion']} · {prep['n']:,} pasajeros ({prep['alta']:,} de prioridad alta) · umbral {t:.2f}")

    st.markdown("#### Lista priorizada de pasajeros")
    if security.can(role, "ver_individual") and security.pseudonym(0):
        top = al.sort_values("p", ascending=False).head(25)
        st.caption("Identificadores protegidos (seudónimos HMAC). Sin opción de exportar. Máximo 25 filas.")
        st.table(_priority_table(ctx, top, lambda r: security.pseudonym(r.Customer_ID)).set_index("Pasajero"))
    else:
        reason = ("Tu sesión no tiene el rol Experiencia del pasajero." if not security.can(role, "ver_individual")
                  else "Falta configurar la sal de seudonimización (pseudonym_salt) en los secretos.")
        st.warning(f"**Acceso restringido.** La lista individual requiere autorización. {reason}")
        st.caption("Para demostrar la vista se muestran pasajeros **FICTICIOS** generados al azar y calificados con el mismo modelo. "
                   "No corresponden a ningún registro real.")
        demo = _demo_passengers(ctx, t)
        st.table(_priority_table(ctx, demo, lambda r: r.id).set_index("Pasajero"))


def _predict(ctx):
    ss = st.session_state
    with st.form("pred_form"):
        st.markdown(f"**Perfil del pasajero** {kind('input')}", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("*Viaje*")
            day = st.selectbox("Día de salida", list(DAYS), index=4, format_func=DAYS.get)
            hour = st.selectbox("Horario", list(HOURS), index=2, format_func=HOURS.get)
            intl = st.radio("Destino", [0, 1], format_func=lambda v: "Internacional" if v else "Nacional", horizontal=True)
            conn = st.radio("Tiene conexión", [1, 0], format_func=lambda v: "Sí" if v else "No", horizontal=True)
            weather = st.radio("Pronóstico de mal clima", [0, 1], format_func=lambda v: "Sí" if v else "No", horizontal=True)
        with c2:
            st.markdown("*Reserva y pasajero*")
            cls = st.selectbox("Clase", list(CLASSES), index=2, format_func=CLASSES.get)
            when = st.selectbox("Anticipación de compra", list(PURCHASE), index=2, format_func=PURCHASE.get)
            age = st.selectbox("Edad", list(AGES), index=4, format_func=AGES.get)
            ff = st.radio("Viajero frecuente", [0, 1], format_func=lambda v: "Sí" if v else "No", horizontal=True)
            biz = st.radio("Viaja por negocios", [0, 1], format_func=lambda v: "Sí" if v else "No", horizontal=True)
        st.caption("«Mal clima + conexión» se calcula automáticamente a partir de las dos respuestas.")
        if st.form_submit_button("Calcular riesgo", type="primary"):
            ss["a_pred"] = {"Age": age, "Booking_Class": cls, "Business_Traveler": biz, "Connections": conn, "Departure_Day": day,
                            "Departure_Hour": hour, "Frequent_Flier_Status": ff, "International_Flight": intl,
                            "When_Ticket_Purchased": when, "Weather_Issues": weather, "Weather_Issues___Connection": int(weather and conn)}
    row = ss.get("a_pred")
    if not row:
        st.info("Completa el perfil y pulsa **Calcular riesgo**.")
        return
    t = _threshold(ctx)
    p = float(lr_probability(pd.DataFrame([row]), ctx.tm.lr_coef, ctx.tm.lr_intercept)[0])
    cat = ("Alto", "bad") if p >= max(0.6, t * 1.5) else (("Medio", "warn") if p >= t else ("Bajo", "ok"))
    rid = iv.assign(pd.DataFrame([row])).iloc[0]
    kpis([
        kpi_html("Probabilidad de no presentarse", pct(p), f"Modelo: {ctx.tm.selected}", "pred", cat[1], f"Riesgo {cat[0]}", lead=True),
        kpi_html("Frente al promedio", f"{p / ctx.overall:.1f} ×", f"promedio histórico {pct(ctx.overall)}", "deriv", cat[1]),
        kpi_html("Acción sugerida", iv.RULE_BY_ID[rid]["intervencion"] if p >= t else "Recordatorio estándar",
                 f"Regla {rid}" if p >= t else f"bajo el umbral de alerta ({t:.2f})", "deriv"),
    ])
    c = lr_contributions(row, ctx.tm.lr_coef, ctx.ref_logits)
    c["etiqueta"] = [VALUE_LABELS[v][int(x)] for v, x in zip(c.variable, c.valor)]
    c = c.reindex(c.contribucion.abs().sort_values(ascending=False).index).head(8)
    st.markdown(f"**Factores que suben o bajan su riesgo** {kind('pred')}", unsafe_allow_html=True)
    st.caption("Contribución exacta de la regresión logística en log-odds frente al pasajero promedio de entrenamiento. Se muestran las 8 mayores.")
    st.plotly_chart(charts.contrib_bars(c), use_container_width=True, config=charts.CONFIG)
    st.markdown("**Limitaciones:** es una probabilidad, no una certeza; explica al modelo, no las razones del pasajero; las variables "
                "describen asociaciones, no causas. No uses edad como único criterio para intervenir.")
    ficha(FICHAS["contrib"])


def _close(ctx):
    ss = st.session_state
    t = _threshold(ctx)
    prep = ss.get("a_interv")
    seg = segment_table(ctx.df, ctx.info.sha256)
    seg = seg[seg.registros >= MIN_N].sort_values("tasa", ascending=False).iloc[0]
    summary("Cierre · Prioridades de contacto", {
        "Hallazgo principal": f"{seg.segmento} tiene la mayor tasa observada: {pct(seg.tasa)} (n = {seg.registros:,}).",
        "Decisión recomendada": (f"{iv.RULE_BY_ID[prep['rid']]['intervencion']} para {prep['n']:,} pasajeros con alerta."
                                 if prep else "Elegir un segmento en la pestaña Intervenciones y preparar la intervención."),
        "Evidencia": f"Umbral {t:.2f}; las alertas tienen la precision y el recall que reporta Anna.",
        "Riesgos y limitaciones": "Correlación, no causa; segmentos traslapados; lista individual solo con autorización.",
        "Siguiente acción": "Coordinar mensaje y canal con el equipo de contacto y medir la tasa de presentación del grupo.",
    }, "al-close")
    if prep:
        final_state("Segmento priorizado e intervención preparada", iv.RULE_BY_ID[prep["rid"]]["intervencion"])


def render(ctx, role):
    t = _threshold(ctx)
    seg = segment_table(ctx.df, ctx.info.sha256)
    seg = seg[seg.registros >= MIN_N]
    top = seg.sort_values("tasa", ascending=False).iloc[0]
    d = _portfolio(ctx, t)
    al = d[d.alerta]
    r1 = al[al.regla == "R1"]
    summary("Resumen ejecutivo", {
        "Hallazgo": f"{top.segmento}: {pct(top.tasa)} de no-show, {(top.tasa - ctx.overall) * 100:+.1f} pp vs. promedio (n = {top.registros:,}).",
        "Indicador de respaldo": f"{len(al):,} de {len(d):,} pasajeros de evaluación tienen alerta con umbral {t:.2f}.",
        "Recomendación": f"Empezar por R1 (mal clima + conexión): {len(r1):,} pasajeros con alerta." if len(r1) >= MIN_N
        else "Priorizar la intervención con más no-shows esperados.",
        "Limitación": "Las tasas son asociaciones históricas; no prueban causa.",
    })
    t1, t2, t3, t4 = st.tabs(["Segmentos", "Intervenciones", "Predicción de un pasajero", "Cierre"])
    with t1:
        _segments(ctx)
    with t2:
        _interventions(ctx, role)
    with t3:
        _predict(ctx)
    with t4:
        _close(ctx)
