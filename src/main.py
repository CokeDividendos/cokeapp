import streamlit as st

st.set_page_config(
    page_title="Plataforma de Análisis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
from . import ui   # debe ir DESPUÉS del set_page_config

def main():
    ui.render()

if __name__ == "__main__":
    main()
