# src/main.py
from .ui import render
import streamlit as st

def main():
    # Configura la página en modo ancho
    st.set_page_config(layout="wide")

    # Barra lateral simple con botones para elegir la sección
    with st.sidebar:
        st.markdown(
            "<h2 style='color:#223354;margin-bottom:1em;'>Menú</h2>",
            unsafe_allow_html=True
        )
        # Recupera la sección seleccionada o usa una por defecto
        section = st.session_state.get("selected_section", "Valoración y Análisis Financiero")

        # Botones para cada sección
        if st.button("Valoración y Análisis Financiero", key="btn_analisis"):
            section = "Valoración y Análisis Financiero"
        if st.button("Seguimiento de Cartera", key="btn_cartera"):
            section = "Seguimiento de Cartera"
        if st.button("Analizar ETF's", key="btn_etf"):
            section = "Analizar ETF's"
        if st.button("Finanzas Personales", key="btn_finanzas"):
            section = "Finanzas Personales"
        if st.button("Calculadora de Interés Compuesto", key="btn_calc"):
            section = "Calculadora de Interés Compuesto"

        st.session_state["selected_section"] = section

    # Renderiza la sección seleccionada
    if section == "Valoración y Análisis Financiero":
        render()
    else:
        st.info("Sección en construcción")
