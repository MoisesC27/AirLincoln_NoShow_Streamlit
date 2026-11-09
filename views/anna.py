"""Anna · Operación y calidad: evaluación del modelo, ajuste de alertas, calidad de datos y decisión del corte."""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import roc_auc_score

from core import security
from core.catalog import ID_COL, PARTITION_LABELS, TARGET
from core.content import FICHAS, SURVEILLANCE
from core.model import AUC_TIE, bootstrap_auc_diff, calibration_bins, confusion, segment_diagnostics
from core.quality import FAIL, MAX_ECE, MIN_AUC_TEST, OK, psi_table
from ui import charts
from ui.theme import final_state, ficha, kind, kpi_html, kpis, num, pct, summary


@st.cache_data(show_spinner="Calculando intervalos por bootstrap…")
def _auc_ci(_ctx, key: str) -> pd.DataFrame:
    df = _ctx.df; te = df.part == "test"; y = df.loc[te, TARGET].to_numpy()
    sel = _ctx.tm.selected
    rng = np.random.default_rng(42)
    rows = []
    for name, p in _ctx.tm.probs.items():
        pp = p[te].to_numpy()
        boots = []
        for _ in range(400):
            idx = rng.integers(0, len(y), len(y))
            if y[idx].min() != y[idx].max():
                boots.append(roc_auc_score(y[idx], pp[idx]))
        lo, hi = np.percentile(boots, [2.5, 97.5])
        diff = bootstrap_auc_diff(y, _ctx.tm.probs[sel][te], pp) if name != sel else None
        rows.append({"modelo": name, "auc": roc_auc_score(y, pp), "ic_bajo": lo, "ic_alto": hi, "seleccionado": name == sel, "diff": diff})
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def _curve(_ctx, part: str, key: str) -> pd.DataFrame:
    s = _ctx.df.part == part
    y, p = _ctx.df.loc[s, TARGET], _ctx.p[s]
    return pd.DataFrame([confusion(y, p, t) for t in np.round(np.arange(0.05, 0.901, 0.01), 2)])


def _evaluation(ctx):
    m = ctx.tm.metrics
    sel = ctx.tm.selected
    r = m[(m.modelo == sel) & (m.conjunto == "test")].iloc[0]
    kpis([
        kpi_html("Distingue a quien falta (AUC)", f"{r.auc:.2f}", "en datos que el modelo no vio", "deriv",
                 "ok" if r.auc >= 0.85 else ("warn" if r.auc >= MIN_AUC_TEST else "bad"),
                 "Excelente" if r.auc >= 0.85 else ("Aceptable" if r.auc >= MIN_AUC_TEST else "Insuficiente")),
        kpi_html("No-shows que detecta", f"{round(r.recall * 10)} de 10", "con el umbral recomendado (prueba)", "deriv",
                 "ok" if r.recall >= 0.6 else ("warn" if r.recall >= 0.4 else "bad"), "Bien" if r.recall >= 0.6 else "Mejorable"),
        kpi_html("Alertas que aciertan", f"{round(r.precision * 10)} de 10", "de los pasajeros marcados (prueba)", "deriv",
                 "ok" if r.precision >= 0.55 else ("warn" if r.precision >= 0.4 else "bad"), "Bien" if r.precision >= 0.55 else "Mejorable"),
        kpi_html("Probabilidades realistas", "Sí" if r.ece <= MAX_ECE else "Revisar", f"error medio de {r.ece * 100:.1f} puntos", "deriv",
                 "ok" if r.ece <= MAX_ECE else "warn", "Calibrado" if r.ece <= MAX_ECE else "Descalibrado"),
    ])
    piv = m.pivot(index="modelo", columns="conjunto")
    tab = pd.DataFrame({
        "AUC entrenamiento": piv[("auc", "train")], "AUC validación": piv[("auc", "valid")], "AUC prueba": piv[("auc", "test")],
        "Precision prueba": piv[("precision", "test")], "Recall prueba": piv[("recall", "test")], "F1 prueba": piv[("f1", "test")],
        "KS prueba": piv[("ks", "test")], "Brier prueba": piv[("brier", "test")], "ECE prueba": piv[("ece", "test")],
        "Umbral (F1 en validación)": piv[("umbral", "test")],
    }).sort_values("AUC validación", ascending=False)
    tab.index = [f"✓ {i}" if i == sel else i for i in tab.index]
    n = m[m.modelo == sel].set_index("conjunto")
    st.markdown(f"**Métricas por modelo y partición** {kind('deriv')}", unsafe_allow_html=True)
    st.caption(f"Entrenamiento {n.loc['train', 'n']:,} · Validación {n.loc['valid', 'n']:,} · Prueba {n.loc['test', 'n']:,} pasajeros "
               f"({n.loc['test', 'positivos']} no-shows en prueba). Precision, recall y F1 usan el umbral de cada modelo.")
    st.dataframe(tab.style.format("{:.3f}"), use_container_width=True)
    st.markdown(f"**Regla de selección:** {ctx.tm.selection_reason}")

    ci = _auc_ci(ctx, ctx.info.sha256)
    st.markdown(f"**AUC en prueba con intervalo de confianza** {kind('deriv')}", unsafe_allow_html=True)
    st.plotly_chart(charts.auc_dots(ci), use_container_width=True, config=charts.CONFIG)
    lines = []
    for r in ci[~ci.seleccionado].itertuples():
        d = r.diff
        verdict = "diferencia significativa" if d["significativa"] else "diferencia **no significativa** (el IC cruza 0)"
        lines.append(f"- {sel} − {r.modelo}: {d['diff']:+.3f} (IC 95% {d['lo']:+.3f} a {d['hi']:+.3f}) → {verdict}.")
    st.markdown("\n".join(lines))
    st.caption(f"Diferencias de AUC menores a {AUC_TIE} se tratan como empate práctico aunque el intervalo no cruce 0.")
    ficha(FICHAS["modelos"])

    te = ctx.df.part == "test"
    cb = calibration_bins(ctx.df.loc[te, TARGET], ctx.p[te])
    ece_v = float(m[(m.modelo == sel) & (m.conjunto == "test")].ece.iloc[0])
    st.markdown(f"**Calibración en prueba** {kind('pred')}", unsafe_allow_html=True)
    st.caption(f"ECE = {ece_v:.3f} (máximo aceptado {MAX_ECE}). Tamaño del punto proporcional a n.")
    st.plotly_chart(charts.calibration(cb), use_container_width=True, config=charts.CONFIG)
    ficha(FICHAS["calibracion"])

    st.markdown(f"**Dónde funciona bien el modelo (prueba)** {kind('deriv')}", unsafe_allow_html=True)
    dg = segment_diagnostics(ctx.df, ctx.p, float(st.session_state.w_umbral))
    show = pd.DataFrame({
        "Segmento": dg.segmento, "n": dg.n, "No-shows": dg.positivos,
        "AUC": [f"{a:.3f}" if c and a == a else "—" for a, c in zip(dg.auc, dg.confiable)],
        "Recall": [pct(r) if c and r == r else "—" for r, c in zip(dg.recall, dg.confiable)],
        "Confianza": np.where(dg.confiable, "✓ Suficiente", "! Incierto (< 10 no-shows o n < 30)"),
    })
    st.dataframe(show, hide_index=True, use_container_width=True)
    ficha(FICHAS["diagnostico"])


def _alerts(ctx):
    ss = st.session_state
    c1, c2 = st.columns([2, 1])
    c1.radio("Conjunto evaluado", ["test", "valid"], format_func=lambda p: f"{PARTITION_LABELS[p]}", key="w_n_part", horizontal=True,
             help="Validación se usó para elegir el umbral; prueba es independiente.")
    c2.button("Usar umbral recomendado", use_container_width=True,
              on_click=lambda: ss.update(w_umbral=ctx.t_rec))
    st.slider("Umbral de alerta", 0.05, 0.90, step=0.01, key="w_umbral",
              help="Probabilidad mínima para marcar a un pasajero. Se comparte con la vista de Armando.")
    t = float(ss.w_umbral)
    part = ss.w_n_part
    s = ctx.df.part == part
    c = confusion(ctx.df.loc[s, TARGET], ctx.p[s], t)
    st.caption(f"Umbral recomendado {ctx.t_rec:.2f}: maximiza F1 (equilibrio entre precision y recall) en validación. "
               f"Conjunto mostrado: {PARTITION_LABELS[part]} ({c['n']:,} pasajeros, {c['positivos']:,} no-shows).")
    total_ok = c["vp"] + c["fp"] + c["fn"] + c["vn"] == c["n"] == int(s.sum())
    kpis([
        kpi_html("No-shows detectados (recall)", pct(c["recall"]), f"{c['vp']:,} de {c['positivos']:,} no-shows", "deriv",
                 "ok" if c["recall"] >= 0.6 else "warn", "≥ 60%" if c["recall"] >= 0.6 else "< 60%", lead=True),
        kpi_html("Alertas correctas (precision)", pct(c["precision"]), f"{c['vp']:,} de {c['alertas']:,} alertas", "deriv",
                 "ok" if c["precision"] >= 0.55 else "warn", "≥ 55%" if c["precision"] >= 0.55 else "< 55%"),
        kpi_html("Pasajeros con alerta", pct(c["pct_alertas"]), f"{c['alertas']:,} de {c['n']:,}", "deriv"),
        kpi_html("No-shows no detectados", num(c["fn"]), "sin alerta y faltaron", "deriv"),
    ])
    st.markdown(f"""<div class="al-conf" role="table" aria-label="Matriz de confusión">
<div class="h"></div><div class="h">Real: no se presentó</div><div class="h">Real: se presentó</div>
<div class="h">Con alerta</div><div><span class="n">{c['vp']:,}</span>✓ Detectados (VP)</div><div><span class="n">{c['fp']:,}</span>! Falsas alarmas (FP)</div>
<div class="h">Sin alerta</div><div><span class="n">{c['fn']:,}</span>✕ No detectados (FN)</div><div><span class="n">{c['vn']:,}</span>✓ Correctos (VN)</div>
</div>""", unsafe_allow_html=True)
    st.caption(f"Comprobación: {c['vp']:,} + {c['fp']:,} + {c['fn']:,} + {c['vn']:,} = {c['n']:,} "
               f"{'✓ coincide' if total_ok else '✕ NO coincide'} con el tamaño de {PARTITION_LABELS[part].lower()}.")
    ficha(FICHAS["matriz"])
    cur = _curve(ctx, part, ctx.info.sha256)
    st.markdown(f"**Más detecciones implican más falsas alarmas** {kind('deriv')}", unsafe_allow_html=True)
    st.plotly_chart(charts.threshold_tradeoff(cur, t, ctx.t_rec), use_container_width=True, config=charts.CONFIG)
    rec = confusion(ctx.df.loc[s, TARGET], ctx.p[s], ctx.t_rec)
    st.markdown(f"Frente al recomendado ({ctx.t_rec:.2f}): {c['vp'] - rec['vp']:+,} detectados y {c['fp'] - rec['fp']:+,} falsas alarmas.")
    ficha(FICHAS["umbral"])


def _quality(ctx, role):
    d = ctx.info
    parts = ctx.df.part.value_counts()
    kpis([
        kpi_html("Archivo", d.file_name, f"SHA-256 {d.sha256[:12]}…", "hist"),
        kpi_html("Registros revisados", num(d.rows), f"{d.columns} columnas · cargado {d.loaded_at}", "hist"),
        kpi_html("Periodo", "Sin fecha", "el dataset no incluye fechas de vuelo", "hist", "warn", "No verificable"),
        kpi_html("Partición", f"{parts.get('train', 0):,} / {parts.get('valid', 0):,} / {parts.get('test', 0):,}", d.partition_source, "deriv"),
    ])
    ch = ctx.checks.sort_values(["orden"])
    icon = {OK: "✓ Cumple", "Advertencia": "! Advertencia", FAIL: "✕ No cumple"}
    st.markdown(f"**Validaciones del corte** {kind('deriv')}", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({"Validación": ch.validacion, "Resultado": ch.resultado, "Estado": ch.estado.map(icon),
                               "Severidad": ch.severidad, "Consecuencia para las predicciones": ch.consecuencia,
                               "Acción recomendada": ch.accion}), hide_index=True, use_container_width=True)
    st.caption("Filas idénticas = todas las columnas iguales, incluido Customer_ID (duplicado real). Customer_ID repetido = mismo "
               "identificador con datos distintos. Perfiles repetidos sin ID = pasajeros distintos con iguales categorías (esperable).")
    if security.can(role, "ver_detalle_calidad") and security.pseudonym(0):
        rep = ctx.df[ctx.df[ID_COL].duplicated(keep=False)]
        st.table(pd.DataFrame({"ID protegido": rep[ID_COL].map(security.pseudonym), "Partición": rep.part.map(PARTITION_LABELS)})
                 .drop_duplicates().set_index("ID protegido"))
    else:
        st.caption("El detalle de Customer_ID repetidos es restringido (rol Operación y calidad).")
    ps = psi_table(ctx.df)
    st.markdown(f"**Estabilidad entre entrenamiento y evaluación (PSI)** {kind('deriv')}", unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({"Variable": ps.variable, "PSI": ps.psi.round(4),
                               "Estado": ps.estado.map({"Estable": "✓ Estable", "Vigilar": "! Vigilar", "Reentrenar": "✕ Reentrenar"})}),
                 hide_index=True, use_container_width=True)
    ficha(FICHAS["psi"])
    st.markdown("#### Frecuencia de vigilancia")
    st.caption("Propuesta del equipo; pendiente de aprobación según la disponibilidad real de datos.")
    st.table(pd.DataFrame(SURVEILLANCE).set_index("Momento"))


def _decision(ctx, role):
    ss = st.session_state
    tone = {"Aceptado": "ok", "Aceptado con observaciones": "warn", "Bloqueado": "bad"}[ctx.gate_status]
    final_state(f"Corte {ctx.gate_status.lower()}", "Estado calculado con reglas verificables", tone)
    st.markdown(f"""**Regla:** cualquier validación de severidad *Crítica* que no cumple bloquea el corte; advertencias o fallas no
críticas lo aceptan con observaciones. Umbrales propuestos: AUC de prueba ≥ {MIN_AUC_TEST}, ECE ≤ {MAX_ECE}, PSI < 0.25,
cero Customer_ID compartidos entre particiones.""")
    if ctx.gate_reasons:
        st.markdown("**Razones:**\n" + "\n".join(f"- {r}" for r in ctx.gate_reasons))
    if security.can(role, "decidir_corte"):
        with st.form("decision"):
            dec = st.radio("Decisión", ["Aceptar corte", "Bloquear corte"], horizontal=True,
                           index=1 if ctx.gate_status == "Bloqueado" else 0)
            why = st.text_area("Motivo (obligatorio)", max_chars=500)
            if st.form_submit_button("Registrar decisión", type="primary"):
                if not why.strip():
                    st.error("Escribe el motivo de la decisión.")
                elif dec == "Aceptar corte" and ctx.gate_status == "Bloqueado":
                    st.error("No se puede aceptar un corte bloqueado por una validación crítica.")
                else:
                    ss["n_decision"] = {"dec": dec, "why": why.strip(), "sha": ctx.info.sha256[:8]}
        if ss.get("n_decision"):
            dd = ss["n_decision"]
            final_state(f"Decisión registrada: {dd['dec'].lower()}", f"versión {dd['sha']} · {dd['why']}",
                        "ok" if dd["dec"].startswith("Aceptar") else "bad")
            st.caption("Registro de esta sesión; no se guarda en una base de datos.")
    else:
        st.caption("Registrar la decisión requiere iniciar sesión con el rol Operación y calidad. El estado calculado es visible para todos.")


def render(ctx, role):
    sel = ctx.tm.selected
    m = ctx.tm.metrics.set_index(["modelo", "conjunto"])
    te = ctx.df.part == "test"
    c = confusion(ctx.df.loc[te, TARGET], ctx.p[te], float(st.session_state.w_umbral))
    summary("Resumen ejecutivo", {
        "Hallazgo": f"Corte {ctx.gate_status.lower()}; {sum(ctx.checks.estado != OK)} validaciones con observaciones, "
                    f"{sum((ctx.checks.estado == FAIL) & (ctx.checks.severidad == 'Crítica'))} críticas.",
        "Indicador de respaldo": f"{sel}: AUC prueba {m.loc[(sel, 'test'), 'auc']:.3f}; con umbral {c['umbral']:.2f} detecta "
                                 f"{c['vp']} de {c['positivos']} no-shows y acierta {c['vp']} de {c['alertas']} alertas (prueba).",
        "Recomendación": "Usar las predicciones con el umbral recomendado y resolver las observaciones pendientes."
        if ctx.gate_status != "Bloqueado" else "No usar las predicciones hasta corregir las fallas críticas.",
        "Limitación": "No se puede verificar que el clima se conozca antes del vuelo; sin fechas no hay deriva temporal.",
    })
    t1, t2, t3, t4 = st.tabs(["1 · Evaluación del modelo", "2 · Ajuste de alertas", "3 · Calidad de datos", "Decisión del corte"])
    with t1:
        _evaluation(ctx)
    with t2:
        _alerts(ctx)
    with t3:
        _quality(ctx, role)
    with t4:
        _decision(ctx, role)
