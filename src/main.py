from .auth import login_required, is_admin, is_premium, is_free, get_nombre_usuario, get_tipo_plan, guardar_api_key_free, logout_button
from .ui import render_dashboard, render_analisis_empresas, render_seguimiento_cartera, render_analizar_etfs
import streamlit as st

def main():
    st.set_page_config(layout="wide")

    if login_required():
        st.sidebar.markdown(
            "<h2 style='color:#223354;margin-bottom:0.7em;'>Menú</h2>",
            unsafe_allow_html=True
        )

        # Navegación principal
        page = st.sidebar.radio(
            "",
            (
                "Dashboard",
                "Análisis de Empresas",
                "Seguimiento de Cartera",
                "Analizar ETFs"
            ),
            key="menu_radio"
        )

        # Espacio empujador para forzar lo siguiente abajo del todo
        st.sidebar.markdown("<div style='height: 220px;'></div>", unsafe_allow_html=True)

        # Sección de tipo de usuario y API key
        with st.sidebar:
            tipo = get_tipo_plan()
            nombre = get_nombre_usuario()
            if tipo == "admin":
                st.markdown(f"<span style='color:#FF8800;font-weight:bold;'>Administrador</span>", unsafe_allow_html=True)
            elif tipo == "premium":
                st.markdown("Cuenta <span style='color:#FF8800;font-weight:bold;'>Premium</span>", unsafe_allow_html=True)
            elif tipo == "free":
                st.markdown("Cuenta <span style='color:#FF8800;font-weight:bold;'>Free</span>", unsafe_allow_html=True)
                st.markdown("🔑 <b>Para utilizar análisis:</b>", unsafe_allow_html=True)
                api_key = st.text_input("Ingresa tu API key de YF", type="password", value="", key="api_key_input")
                if st.button("Guardar API Key"):
                    guardar_api_key_free(api_key)
                    st.success("API Key guardada correctamente.")

        # Cerrar sesión lo más abajo posible
        st.sidebar.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
        st.sidebar.markdown("---")
        logout_placeholder = st.sidebar.empty()
        with logout_placeholder:
            logout_button()

        # Cabecera principal
        nombre = get_nombre_usuario()
        st.markdown(
            f"""
            <h1 style="margin-bottom:0.6em;">
              Bienvenido a <span style="color:#FF8800;">Dividends Up!</span> {nombre if nombre else ""}
            </h1>
            """,
            unsafe_allow_html=True
        )

        # Render según selección
        if page == "Dashboard":
            render_dashboard()
        elif page == "Análisis de Empresas":
            render_analisis_empresas()
        elif page == "Seguimiento de Cartera":
            render_seguimiento_cartera()
        elif page == "Analizar ETFs":
            render_analizar_etfs()
