# main.py
from .auth import (
    login_required,
    get_nombre_usuario,
    get_tipo_plan,
    logout_button,
)
from .ui import render
import streamlit as st

import src.db as db  # Ajusta el import si tu estructura de carpetas es diferente

def main():
    # 1. Configuración de página en modo wide
    st.set_page_config(layout="wide")

    if login_required():
        # 2. Barra lateral profesional con botones
        with st.sidebar:
            st.markdown(
                "<h2 style='color:#223354;margin-bottom:1em;'>Menú</h2>",
                unsafe_allow_html=True
            )
             
            # Botones con estilo profesional
            section = st.session_state.get("selected_section", "Valoración y Análisis Financiero")
            btn1 = st.button("Valoración y Análisis Financiero", use_container_width=True, key="btn_analisis")
            btn2 = st.button("Seguimiento de Cartera", use_container_width=True, key="btn_cartera")
            btn3 = st.button("Analizar ETF's", use_container_width=True, key="btn_etf")
            btn4 = st.button("Finanzas Personales", use_container_width=True, key="btn_finanzas")
            btn5 = st.button("Calculadora de Interés Compuesto", use_container_width=True, key="btn_calc")

            if btn1:
                section = "Valoración y Análisis Financiero"
            elif btn2:
                section = "Seguimiento de Cartera"
            elif btn3:
                section = "Analizar ETF's"
            elif btn4:
                section = "Finanzas Personales"
            elif btn5:
                section = "Calculadora de Interés Compuesto"
            st.session_state["selected_section"] = section

            st.markdown("---")
            tipo = get_tipo_plan()
            if tipo == "admin":
                st.markdown(
                    f"<span style='color:#FF8800;font-weight:bold;'>Administrador</span>",
                    unsafe_allow_html=True,
                )
            elif tipo == "premium":
                st.markdown(
                    "Cuenta <span style='color:#FF8800;font-weight:bold;'>Premium</span>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "Cuenta <span style='color:#FF8800;font-weight:bold;'>Free</span>",
                    unsafe_allow_html=True,
                )
            st.markdown("---")

            logout_button()  # Botón al final

        # 3. Encabezado principal con nombre
        nombre = get_nombre_usuario()
        st.markdown(
            f"""
            <h1 style="margin-bottom:0.6em;">
              Bienvenido a <span style="color:#FF8800;">Dividends Up!</span> {nombre or ""}
            </h1>
            """,
            unsafe_allow_html=True,
        )

        # 4. Renderizado de sección única principal
        # Solo muestra la UI principal, elimina tabs internos (lo hace render())
        if section == "Valoración y Análisis Financiero":
            render()
        else:
            st.info("Sección en construcción")
