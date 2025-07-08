# main.py
from .auth import (
    login_required,
    get_nombre_usuario,
    get_tipo_plan,
    logout_button,
)
from .ui import render
import streamlit as st

def main():
    # 1. Configuración de página en modo wide
    st.set_page_config(layout="wide")

    if login_required():
        # 2. Barra lateral con navegación y datos de cuenta
        with st.sidebar:
            selected_tab = st.radio(
                "Secciones",
                [
                    "Valoración y Análisis Financiero",
                    "Seguimiento de Cartera",
                    "Analizar ETF's",
                    "Finanzas Personales",
                    "Calculadora de Interés Compuesto",
                ],
            )

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
            logout_button()

        # 3. Encabezado principal
        nombre = get_nombre_usuario()
        st.markdown(
            f"""
            <h1 style="margin-bottom:0.6em;">
              Bienvenido a <span style="color:#FF8800;">Dividends Up!</span> {nombre or ""}
            </h1>
            """,
            unsafe_allow_html=True,
        )

        # 4. Renderizado de sección
        if selected_tab == "Valoración y Análisis Financiero":
            render()
        else:
            st.info("Sección en construcción")

