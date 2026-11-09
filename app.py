"""Air Lincoln · Dashboard de no-show en Streamlit.

El diseño es la plantilla ui/dashboard_template.html. Los datos salen de data/AIRLINCOLNDATA2.csv
y los modelos se entrenan en Python (core/) cada vez que cambia el archivo.

Ejecutar:  streamlit run app.py
"""
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Air Lincoln No-Show", page_icon="✈️", layout="wide", initial_sidebar_state="collapsed")

from core.context import load_context  # noqa: E402
from core.data import DataError  # noqa: E402
from core.payload import build_payload  # noqa: E402

TEMPLATE = Path(__file__).parent / "ui" / "dashboard_template.html"

st.markdown("""<style>
.block-container { padding: 0.5rem 0.75rem 0 0.75rem; max-width: 100%; }
header[data-testid="stHeader"] { display: none; }
footer { visibility: hidden; }
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Ajustes")
    alto = st.slider("Alto del dashboard (px)", min_value=600, max_value=1400, value=820, step=20)
    if st.button("Volver a cargar datos y modelos"):
        st.cache_resource.clear()
        st.cache_data.clear()
        st.rerun()

try:
    ctx = load_context()
except DataError as exc:
    st.error(f"No se pudieron cargar los datos: {exc}")
    st.info("Coloca el archivo en data/AIRLINCOLNDATA2.csv y pulsa «Volver a cargar» en la barra lateral.")
    st.stop()


@st.cache_data(show_spinner=False)
def page(sha: str) -> str:
    data = json.dumps(build_payload(ctx), separators=(",", ":"), ensure_ascii=False)
    return TEMPLATE.read_text(encoding="utf-8").replace("/*DATA*/", data)


html = page(ctx.info.sha256)
if hasattr(st, "iframe"):
    st.iframe(html, height=alto)
else:
    components.html(html, height=alto, scrolling=True)
