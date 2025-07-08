from .auth import (
    login_required,
    get_nombre_usuario,
    get_tipo_plan,
    logout_button,
)
from .ui import render
import streamlit as st
import src.db as db

def main():
    st.set_page_config(layout="wide")
    if login_required():
        with st.sidebar:
            st.markdown(
                "<h2 style='color:#223354;margin-bottom:1em;'>Menú</h2>",
                unsafe_allow_html=True
            )
            # Debug temporal de usuario — puedes quitarlo luego
            st.write("Usuario actual:", st.session_state.get("user"))
            st.write("Registro DB:", st.session_state.get("user_db"))

            section = st.session_state.get("selected_section", "Valoración y Análisis Financiero")
            btn1 = st.button("Valoración y Análisis Financiero", key="btn_analisis")
            btn2 = st.button("Seguimiento de Cartera", key="btn_cartera")
            btn3 = st.button("Analizar ETF's", key="btn_etf")
            btn4 = st.button("Finanzas Personales", key="btn_finanzas")
            btn5 = st.button("Calculadora de Interés Compuesto", key="btn_calc")

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

            # Botón de usuarios registrados solo para admins (opcional)
            if tipo == "admin":
                if st.button("Ver usuarios registrados"):
                    usuarios = db.listar_usuarios()
                    st.write("Usuarios registrados:")
                    for u in usuarios:
                        st.write(f"ID: {u[0]}, Email: {u[1]}, Nombre: {u[2]}")

            logout_button()
        
        # Encabezado principal con nombre del usuario logueado
        nombre = get_nombre_usuario()
        st.markdown(
            f"""
            <h1 style="margin-bottom:0.6em;">
              Bienvenido a <span style="color:#FF8800;">Dividends Up!</span> {nombre or ""}
            </h1>
            """,
            unsafe_allow_html=True,
        )

        # Render de la UI principal
        if section == "Valoración y Análisis Financiero":
            render()
        else:
            st.info("Sección en construcción")
