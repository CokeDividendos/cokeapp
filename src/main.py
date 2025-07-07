from .auth import login_required, logout_button
from .ui import render  # <-- Agrega esta línea
import streamlit as st

def main():
    if login_required():
        logout_button()
        st.title("Bienvenido a CokeApp")
        st.write(f"¡Hola, {st.session_state['user']}!")
        render()  # <-- Agrega esta línea para mostrar la app principal
