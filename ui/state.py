"""Valores por defecto de los controles y persistencia al cambiar de perfil.

Streamlit borra el valor de un control cuando deja de mostrarse (por ejemplo, al cambiar de perfil).
Guardamos una copia en claves "_p_<clave>" al final de cada ejecución y la restauramos al inicio.
"""
import streamlit as st

DEFAULTS = {
    "w_persona": "laura",
    # Laura · simulador
    "w_l_dia": 5, "w_l_hora": 3, "w_l_hub": 1, "w_l_intl": 0, "w_l_clima": "hist",
    "w_l_cap": 180, "w_l_cv": 2500, "w_l_cn": 9000,
    "w_l_base": "modelo", "w_l_tol_on": False, "w_l_tol": 10, "w_l_manual": 20, "w_l_ampliar": False,
    # Laura · mapa
    "w_m_hub": "Todos", "w_m_intl": "Todos",
    # Armando
    "w_a_rule": "R1", "w_a_seg_min": True,
    # Anna
    "w_n_part": "test", "w_umbral": None,  # None → se reemplaza por el umbral recomendado
}

SIM_KEYS = ["w_l_base", "w_l_dia", "w_l_hora", "w_l_hub", "w_l_intl", "w_l_clima", "w_l_cap", "w_l_cv", "w_l_cn",
            "w_l_tol_on", "w_l_tol", "w_l_manual", "w_l_ampliar"]
MAP_KEYS = ["w_m_hub", "w_m_intl"]


def init(recommended_threshold: float) -> None:
    ss = st.session_state
    for k, v in DEFAULTS.items():
        if k not in ss:
            if k == "w_umbral" and v is None:
                v = recommended_threshold
            ss[k] = ss.get("_p_" + k, v)


def snapshot() -> None:
    ss = st.session_state
    for k in DEFAULTS:
        if k in ss:
            ss["_p_" + k] = ss[k]


def reset(keys: list[str], recommended_threshold: float | None = None) -> None:
    ss = st.session_state
    for k in keys:
        v = DEFAULTS[k]
        if k == "w_umbral":
            v = recommended_threshold
        ss[k] = v
        ss["_p_" + k] = v
