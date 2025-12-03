# src/auth.py
import streamlit as st

def login_required() -> bool:
    """
    Stub de autenticación: siempre devuelve True.
    La aplicación se carga sin requerir login.
    """
    return True

def get_nombre_usuario() -> str:
    """
    Devuelve un nombre vacío.
    """
    return ""

def get_tipo_plan() -> str:
    """
    Devuelve un plan vacío o 'free' si prefieres mostrar algo.
    """
    return ""

def logout_button():
    """
    No hace nada. Mantenida por compatibilidad con main.py.
    """
    pass
