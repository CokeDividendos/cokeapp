from .auth import login_required, logout_button, is_admin, is_premium, is_free
from .ui import render
import streamlit as st

def main():
    if login_required():
        logout_button()
        user = st.session_state.get("user_db")
        if is_admin():
            st.info(f"Estás usando la app como administrador ({user[1]})")
        elif is_premium():
            st.success("¡Bienvenido usuario premium!")
        else:
            st.warning("Usuario Free. Algunas funciones requerirán API key de YF.")
        st.title("Bienvenido a Dividends Up!")
        st.write(f"¡Hola, {st.session_state['user']}!")
        render()
