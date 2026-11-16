"""Air Lincoln · Dashboard de no-show en Streamlit.

Flujo:
1. Inicio de sesión: solo Laura, Armando y Anna (contraseñas cifradas en .streamlit/secrets.toml).
2. ¿Qué datos quieres analizar?: se sube un CSV o Excel; se revisa contra el contrato de datos ANTES de dibujar.
3. Dashboard: se entrenan los modelos con ese archivo y se llena la plantilla ui/dashboard_template.html.
   «Cambiar documento» regresa al paso 2 y el dashboard se recalcula con los datos nuevos.

Ejecutar:  streamlit run app.py
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Air Lincoln No-Show", page_icon="✈️", layout="wide", initial_sidebar_state="collapsed")

from core import auth, flight_table, settings  # noqa: E402
from core.contract import check_bytes, contract_table  # noqa: E402
from core.data import DATA_FILE, DataError  # noqa: E402

ROOT = Path(__file__).parent
# Componente de dos vías: dibuja el dashboard y devuelve a Python el umbral que fija Anna.
dashboard_component = components.declare_component("airlincoln_dashboard", path=str(ROOT / "ui" / "component"))
ss = st.session_state

BASE_CSS = """<style>
.block-container { padding: 0.75rem 1rem 1rem 1rem; max-width: 100%; }
header[data-testid="stHeader"] { display: none; }
footer { visibility: hidden; }
</style>"""
st.markdown(BASE_CSS, unsafe_allow_html=True)

LOGIN_CSS = """<style>
[data-testid="stAppViewContainer"] { background: #E9EEF5; }
[data-testid="stForm"] {
  background: linear-gradient(180deg, #9CC9F5 0%, #7FA3C9 45%, #556E8F 100%);
  border: none; border-radius: 18px; padding: 28px 36px 32px; box-shadow: 0 18px 40px rgba(40, 60, 90, .25);
}
[data-testid="stForm"] label p { color: #FFFFFF !important; font-weight: 700; font-size: 1.05rem; }
[data-testid="stForm"] input[type="text"], [data-testid="stForm"] input[type="password"] {
  background: #4A6080 !important; color: #FFFFFF !important; border: none !important; border-radius: 6px;
}
[data-testid="stForm"] div[data-baseweb="input"] { background: #4A6080 !important; border: none !important; border-radius: 6px; }
[data-testid="stForm"] div[data-baseweb="input"] button { background: #4A6080 !important; color: #E8EEF6 !important; }
[data-testid="stForm"] [data-testid="stCheckbox"] p { color: #FFFFFF !important; font-weight: 600; }
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
  background: #3F5675; color: #FFFFFF; border: none; border-radius: 999px; padding: 10px 24px; font-size: 1.15rem;
  font-weight: 800; letter-spacing: .06em; box-shadow: 0 6px 14px rgba(20, 35, 60, .35); margin: 8px auto 0; display: block;
}
[data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover { background: #33475F; color: #FFFFFF; }
[data-testid="stForm"] [data-testid="stFormSubmitButton"] { display: flex; justify-content: center; }
.al-avatar { display: flex; justify-content: center; margin: 4px 0 10px; }
.al-forgot { text-align: right; color: #FFFFFF; font-weight: 600; font-size: .95rem; padding-top: 6px; }
.al-login-title { text-align: center; color: #3F5675; margin: 24px 0 8px; font-weight: 700; font-size: 1.4rem; }
</style>"""

AVATAR = """<div class="al-avatar"><svg width="96" height="96" viewBox="0 0 96 96" role="img" aria-label="Usuario">
<circle cx="48" cy="30" r="20" fill="#435A7A" stroke="#7F9AC0" stroke-width="2"/>
<path d="M10 92c0-22 17-36 38-36s38 14 38 36z" fill="#435A7A" stroke="#7F9AC0" stroke-width="2"/></svg></div>"""


# ---------------------------------------------------------------- 1. Inicio de sesión
def restore_session() -> None:
    if "user" not in ss:
        tok = st.query_params.get("s")
        u = auth.read_token(tok) if tok else None
        if u:
            ss.user = u


def login_screen() -> None:
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.markdown('<div class="al-login-title">Air Lincoln · Inteligencia de No-show</div>', unsafe_allow_html=True)
    if "data_name" in ss:
        st.markdown(f'<p style="text-align:center;color:#3F5675">Inicia sesión para continuar con <b>{ss.data_name}</b>. '
                    'Cada usuario ve solo su sección.</p>', unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.15, 1])
    with mid:
        if not auth.configured():
            st.error("No hay usuarios configurados. Copia `.streamlit/secrets.toml.example` como `.streamlit/secrets.toml` "
                     "y genera las contraseñas con `python scripts/crear_usuario.py`.")
            st.stop()
        with st.form("login"):
            st.markdown(AVATAR, unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="laura, armando o anna")
            password = st.text_input("Password", type="password")
            c1, c2 = st.columns(2)
            remember = c1.checkbox("Remember me")
            c2.markdown('<div class="al-forgot">Forgot Password?</div>', unsafe_allow_html=True)
            _, bmid, _ = st.columns([1, 1.2, 1])
            with bmid:
                submitted = st.form_submit_button("LOGIN", use_container_width=True)
        if st.button("¿Olvidaste tu contraseña?", type="tertiary"):
            st.info("Pide a Anna (administración del tablero) que genere una nueva con `python scripts/crear_usuario.py`.")
        if submitted:
            ss.attempts = ss.get("attempts", 0) + 1
            if ss.attempts > auth.MAX_ATTEMPTS:
                st.error("Demasiados intentos fallidos. Recarga la página para intentar de nuevo.")
                st.stop()
            u = auth.verify(username, password)
            if u:
                ss.user, ss.attempts = u, 0
                if remember:
                    st.query_params["s"] = auth.make_token(u["usuario"])
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos. Solo pueden entrar Laura, Armando y Anna.")


# ---------------------------------------------------------------- 2. ¿Qué datos quieres analizar?
def data_screen() -> None:
    u = ss.user
    st.markdown(f"### Hola, {u['nombre']}. ¿Qué datos quieres analizar?")
    st.caption("Sube un archivo CSV o Excel con las mismas 16 columnas del contrato de datos. Se valida antes de usarlo; "
               "con él se entrenan los modelos y se arma el dashboard.")
    left, right = st.columns([2, 1], gap="large")
    with left:
        up = st.file_uploader("Tu documento (CSV o Excel)", type=["csv", "xlsx", "xls"])
        if up is not None:
            use_file(up.getvalue(), up.name)
    with right:
        with st.container(border=True):
            st.markdown("**¿No tienes un archivo a la mano?**")
            example = DATA_FILE.with_suffix(".xlsx") if DATA_FILE.with_suffix(".xlsx").exists() else DATA_FILE
            st.caption(f"Usa el archivo original del proyecto: {example.name} (10,000 pasajeros, con vuelos y fechas).")
            if st.button("Usar el archivo de ejemplo", use_container_width=True):
                use_file(example.read_bytes(), example.name)
        with st.expander("Columnas que debe tener el archivo"):
            st.dataframe(contract_table(), hide_index=True, use_container_width=True)
    top_bar(show_change=False)


def use_file(data: bytes, name: str) -> None:
    res = check_bytes(data, name) if data else None
    if res is None or not res.usable:
        st.error(f"**{name} no se puede analizar.** Le faltan columnas del contrato o no tiene filas válidas. Corrige el archivo o sube otro.")
        if res is not None:
            for p in res.problems:
                st.markdown(f"- {p}")
            st.dataframe(type_report(res.report), hide_index=True, use_container_width=True)
        return
    ss.data_bytes, ss.data_name = data, name
    st.rerun()


# ---------------------------------------------------------------- 3. Dashboard
def type_report(r: pd.DataFrame) -> pd.DataFrame:
    return r.rename(columns={"columna": "Columna", "tipo_esperado": "Tipo esperado", "tipo_detectado": "Tipo detectado",
                             "texto_no_numerico": "Texto no numérico", "vacios": "Marcas de vacío", "fuera_de_rango": "Fuera de rango",
                             "vacio_significa": "Vacío significa", "estado": "Estado"})


def top_bar(show_change: bool = True) -> None:
    with st.sidebar:
        st.markdown(f"**Sesión:** {ss.user['nombre']}" + (f" · {ss.user['rol']}" if ss.user.get("rol") else ""))
        if "data_name" in ss:
            st.markdown(f"**Datos:** {ss.data_name}")
        if show_change and st.button("Cambiar documento", use_container_width=True):
            for k in ("data_bytes", "data_name"):
                ss.pop(k, None)
            st.rerun()
        if st.button("Cerrar sesión", use_container_width=True):
            for k in ("user", "data_bytes", "data_name"):
                ss.pop(k, None)
            st.query_params.clear()
            st.rerun()


def dashboard() -> None:
    data, name = ss.data_bytes, ss.data_name
    top_bar()
    with st.sidebar:
        st.divider()
        alto = st.slider("Alto del dashboard (px)", min_value=600, max_value=1400, value=820, step=20)

    c1, c2, c3 = st.columns([4, 1, 1], vertical_alignment="center")
    c1.markdown(f"**{ss.user['nombre']}** · {ss.user.get('rol', '')} · analizando **{name}**")
    if c2.button("Cambiar de usuario", key="switch_user", use_container_width=True):
        ss.pop("user", None)          # el documento cargado se conserva
        st.query_params.clear()
        st.rerun()
    if c3.button("Cambiar documento", key="change_top", use_container_width=True):
        for k in ("data_bytes", "data_name"):
            ss.pop(k, None)
        st.rerun()

    # Revisión de tipos ANTES de dibujar
    res = check_bytes(data, name)
    n_ok = int(res.report.estado.str.startswith("✓").sum())
    if res.ok:
        st.success(f"**Revisión de tipos: ✓ cumple el contrato.** {n_ok} de {len(res.report)} columnas cumplen su tipo · "
                   f"{res.invisible_rows} caracteres invisibles corregidos · {res.excluded_rows} filas excluidas por «sin dato» · "
                   f"{len(res.df):,} pasajeros válidos.")
    elif res.usable:
        filas = ", ".join(str(r) for r in res.error_rows[:15]) + (" …" if len(res.error_rows) > 15 else "")
        st.error(f"**Revisión de tipos: ✕ el archivo trae datos que no cumplen el contrato.** "
                 f"{res.invalid_rows} filas con valores inválidos se excluyeron (filas del archivo: {filas}) · "
                 f"{max(0, res.excluded_rows - res.invalid_rows)} filas sin dato excluidas · "
                 f"el tablero muestra solo los {len(res.df):,} pasajeros válidos.")
        st.markdown("\n".join(f"- {p}" for p in res.problems))
    else:
        st.error("**Revisión de tipos: ✕ el archivo no se puede analizar.** " + "; ".join(res.problems))
    with st.expander("Ver la revisión de tipos y el contrato de datos", expanded=not res.usable):
        st.dataframe(type_report(res.report), hide_index=True, use_container_width=True)
        if res.missing_tokens_found:
            st.caption(f"Marcas de «no hay dato» encontradas y convertidas: {res.missing_tokens_found}")
        st.dataframe(contract_table(), hide_index=True, use_container_width=True)
    if not res.usable:
        st.stop()

    from core.context import build_context
    from core.payload import build_payload
    try:
        ctx = build_context(data, name)
    except DataError as exc:
        st.error(f"No se puede analizar este archivo: {exc}")
        st.stop()

    sha, user = ctx.info.sha256, ss.user["usuario"]
    saved = settings.get_threshold(sha)
    thr = saved["umbral"] if saved else ctx.tm.thresholds[ctx.tm.selected]
    if saved:
        st.caption(f"Umbral de alerta vigente: **{thr:.0%}**, fijado por {saved['por'].capitalize()} el {saved['cuando']}. "
                   f"Se aplica en todas las secciones (recomendado: {ctx.t_rec:.0%}).")
    else:
        st.caption(f"Umbral de alerta vigente: **{thr:.0%}** (el recomendado). Anna puede cambiarlo en «Ajustar alertas».")

    payload = build_payload(ctx, user, lock=True, threshold=thr)
    value = dashboard_component(data=payload, height=alto, key=f"dash_{sha[:12]}_{user}", default=None)

    # Anna movió el control: se guarda como umbral oficial para todos los usuarios.
    if value and isinstance(value, dict) and "umbral" in value and value.get("t") != ss.get("last_thr_event"):
        ss.last_thr_event = value.get("t")
        new = round(float(value["umbral"]), 2)
        if user == "anna" and abs(new - thr) > 1e-9:
            when = pd.Timestamp.now(tz="America/Mexico_City").strftime("%d/%m/%Y %H:%M")
            settings.set_threshold(sha, new, user, when)
            st.toast(f"Umbral de alerta guardado: {new:.0%}. Ya se aplica para Laura, Armando y Anna.")
            st.rerun()

    # Tabla de tipos de vuelo (actividad 5) desactivada a petición del equipo.
    # Para mostrarla en la sección de Laura, quitar el comentario de las dos líneas siguientes:
    # if ss.user["usuario"] == "laura":
    #     flight_table_section(ctx)


# ---------------------------------------------------------------- Tabla de Laura (actividad 5)
@st.cache_data(show_spinner="Simulando cada tipo de vuelo…", max_entries=10)
def _flight_table(_ctx, sha: str, cap: int, cv: float, cn: float) -> pd.DataFrame:
    return flight_table.build(_ctx.df, _ctx.p, cap, cv, cn)


def flight_table_section(ctx) -> None:
    st.subheader("Tipos de vuelo: costo de no-show y sobreventa")
    c1, c2, c3 = st.columns(3)
    cap = c1.number_input("Asientos por vuelo", 20, 600, 180, 1, key="t_cap")
    cv = c2.number_input("Costo de asiento vacío (MXN)", 0, 100_000, 2500, 100, key="t_cv")
    cn = c3.number_input("Costo de negar abordaje (MXN)", 0, 200_000, 9000, 100, key="t_cn")
    st.caption("Cada encabezado dice de dónde viene la cifra: [dato] sale del archivo, [calculado] con fórmulas o con el modelo, "
               "[simulado] escenario con los costos de arriba. Haz clic en un encabezado para ordenar. Solo grupos con 30 pasajeros o más.")
    t = _flight_table(ctx, ctx.info.sha256, int(cap), float(cv), float(cn))
    if t.empty:
        st.info("Ningún tipo de vuelo tiene 30 pasajeros o más en este archivo, así que la tabla no se publica.")
        return
    O = flight_table.ORIGIN
    lbl = lambda c: f"{c} [{O[c]}]"  # noqa: E731
    order = ["Día", "Horario", "Salida desde hub", "Destino", "Costo esperado (MXN)", "Diferencia vs. no sobrevender (MXN)",
             "Sobreventa recomendada", "Pasajeros", "No-shows", "Tasa de no-show", "Probabilidad prevista"]
    st.dataframe(
        t, hide_index=True, use_container_width=True, column_order=order,
        column_config={
            "Día": st.column_config.TextColumn(lbl("Día"), help="Departure_Day del archivo"),
            "Horario": st.column_config.TextColumn(lbl("Horario"), help="Departure_Hour del archivo"),
            "Salida desde hub": st.column_config.TextColumn(lbl("Salida desde hub"), help="Major_Hub_Departure del archivo"),
            "Destino": st.column_config.TextColumn(lbl("Destino"), help="International_Flight del archivo"),
            "Pasajeros": st.column_config.NumberColumn(lbl("Pasajeros"), help="Conteo de registros del grupo", format="%d"),
            "No-shows": st.column_config.NumberColumn(lbl("No-shows"), help="Suma de No_Show del grupo", format="%d"),
            "Tasa de no-show": st.column_config.NumberColumn(lbl("Tasa de no-show"), help="No-shows ÷ pasajeros", format="percent"),
            "Probabilidad prevista": st.column_config.NumberColumn(lbl("Probabilidad prevista"),
                                                                   help="Promedio de la probabilidad del modelo", format="percent"),
            "Sobreventa recomendada": st.column_config.NumberColumn(lbl("Sobreventa recomendada"),
                                                                    help="Boletos extra de menor costo esperado", format="+%d"),
            "Costo esperado (MXN)": st.column_config.NumberColumn(lbl("Costo esperado (MXN)"),
                                                                  help="Simulación Beta-binomial con los costos de arriba", format="dollar"),
            "Diferencia vs. no sobrevender (MXN)": st.column_config.NumberColumn(
                lbl("Diferencia vs. no sobrevender (MXN)"), help="Costo sin sobreventa − costo con la sobreventa recomendada",
                format="dollar"),
        },
    )


# ---------------------------------------------------------------- Router
restore_session()
if "user" not in ss:
    login_screen()
elif "data_bytes" not in ss:
    data_screen()
else:
    dashboard()
