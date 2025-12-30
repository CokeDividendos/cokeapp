# src/auth.py

import streamlit as st
from .db import init_user_table, get_user
import hashlib

def hash_password(password: str) -> str:
    """Devuelve el hash SHA256 de la contraseña."""
    return hashlib.sha256(password.encode()).hexdigest()

def login():
    """Formulario de inicio de sesión con correo y contraseña."""
    st.markdown("## Inicia sesión")
    email = st.text_input("Correo electrónico")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if not email or not password:
            st.error("Por favor, introduce correo y contraseña.")
            st.stop()

        usuario = get_user(email)
        if usuario and usuario[1] == hash_password(password):
            # Autenticado correctamente
            st.session_state["user"] = email
            st.success("Sesión iniciada correctamente.")
            st.experimental_rerun()
        else:
            st.error("Correo o contraseña incorrectos.")
            st.stop()
