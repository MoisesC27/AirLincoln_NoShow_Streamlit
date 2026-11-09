"""Acerca del producto: objetivo de negocio, usuarios, recorridos, fichas, alternativas, permisos y glosario."""
import pandas as pd
import streamlit as st

from core import security
from core.content import BUSINESS_GOAL, DISCARDED, FICHAS, GLOSSARY, JOURNEYS, PERSONAS, USER_TABLE
from ui.theme import pct


def render(ctx, role):
    st.markdown("### Objetivo de negocio")
    base = (f"No-show histórico {pct(ctx.overall)} ({ctx.overall_k:,} de {ctx.info.rows:,}): sin sobreventa, ≈{ctx.overall * 100:.0f} "
            "asientos vacíos por cada 100 asientos.")
    st.table(pd.DataFrame([{**g, "Contenido": g["Contenido"].format(baseline=base)} for g in BUSINESS_GOAL]).set_index("Elemento"))

    st.markdown("### Usuarios, problema y decisión")
    st.table(pd.DataFrame(USER_TABLE).set_index("Usuario"))
    cols = st.columns(3)
    for col, p in zip(cols, PERSONAS.values()):
        with col.container(border=True):
            st.markdown(f"**{p['nombre']} · {p['rol']}**")
            st.markdown(f"- **Contexto:** {p['contexto']}\n- **Conocimiento:** {p['conocimiento']}\n- **Necesidad:** {p['necesidad']}\n"
                        f"- **Frecuencia:** {p['frecuencia']}\n- **Estado de éxito:** {p['exito']}")

    st.markdown("### Recorridos y bifurcaciones")
    st.dataframe(pd.DataFrame(JOURNEYS), hide_index=True, use_container_width=True)

    st.markdown("### Alternativas de visualización descartadas")
    st.table(pd.DataFrame(DISCARDED).set_index("Alternativa descartada"))

    st.markdown("### Fichas metodológicas de todas las gráficas")
    st.dataframe(pd.DataFrame([{"Visualización": f["nombre"], "Pregunta": f["pregunta"], "Usuario": f["usuario"],
                                "Variables": f["variables"], "Tipo": f["tipo"], "Por qué": f["porque"],
                                "Alternativa descartada": f["descartada"], "Decisión": f["decision"],
                                "Limitaciones": f["limitaciones"]} for f in FICHAS.values()]),
                 hide_index=True, use_container_width=True)

    st.markdown("### Seguridad y permisos")
    st.markdown("""- **Autenticación** (quién eres): inicio de sesión OIDC de Streamlit, activo solo si `.streamlit/secrets.toml` tiene `[auth]`.
- **Autorización** (qué puedes ver y hacer): rol asignado al correo verificado en `[roles]`. Sin sesión, el rol es *Público*.
- Las funciones que entregan datos individuales comprueban el permiso en el servidor antes de calcularlos; el selector de perfil no da permisos.
- Agregados con menos de 30 registros se suprimen; en el mapa se suprime además una celda complementaria para evitar el cálculo por diferencia.
- Ningún rol puede exportar registros individuales; las listas se muestran con seudónimos (HMAC) y sin botón de descarga.""")
    perms = list(security.PERMISSIONS)
    mat = pd.DataFrame({security.ROLES[r]: ["✓" if p in security.MATRIX[r] else "—" for p in perms] for r in security.ROLES},
                       index=[security.PERMISSIONS[p] for p in perms])
    st.table(mat)
    st.caption(f"Estado actual: autenticación {'configurada' if security.auth_configured() else 'no configurada (vista pública)'}; "
               f"rol de esta sesión: {security.ROLES[role]}.")

    st.markdown("### Glosario")
    st.table(pd.DataFrame({"Término": list(GLOSSARY), "Definición": list(GLOSSARY.values())}).set_index("Término"))

    st.markdown("### Pendientes de verificar")
    st.markdown("- Observaciones del profesor del 21 de octubre que no venían en la información recibida.\n"
                "- Asignación oficial de la partición de Colab (5,999 / 3,001 / 1,000): agregar `data/particion.csv` para reproducirla.\n"
                "- Costos reales de asiento vacío y de negar abordaje.\n- Hora en que se conoce `Weather_Issues`.")
