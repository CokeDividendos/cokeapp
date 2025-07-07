import streamlit as st
st.set_page_config(page_title="Plataforma de Análisis",
                   page_icon="📈",
                   layout="wide",
                   initial_sidebar_state="collapsed")
from . import ui   # solo importamos, sin llamar nada
from .auth import login_required

def main():
    if login_required():
        ui.render()

if __name__ == "__main__":
    main()
