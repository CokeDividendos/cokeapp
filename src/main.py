from .auth import login_required, logout_button, is_admin, is_premium, is_free, get_nombre_usuario, get_tipo_plan, guardar_api_key_free
from .ui import render
import streamlit as st

def main():
    st.set_page_config(layout="wide")  # 1. Modo wide desde el inicio

    if login_required():
        logout_button()

        # Sidebar: tipo de cuenta y campo API Key si es free
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

        nombre = get_nombre_usuario()
        st.markdown(
            f"""
            <h1 style="margin-bottom:0.6em;">
              Bienvenido a <span style="color:#FF8800;">Dividends Up!</span> {f"({nombre})" if nombre else ""}
            </h1>
            """,
            unsafe_allow_html=True
        )
        render()
