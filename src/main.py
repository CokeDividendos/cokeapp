from .auth import login_required, logout_button
import streamlit as st

def main():
    if login_required():
        logout_button()
        st.title("Bienvenido a CokeApp")
        st.write(f"¡Hola, {st.session_state['user']}!")
        # ... Aquí tu UI principal
