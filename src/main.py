import streamlit as st

# 1️⃣ SOLO una vez por app
st.set_page_config(
    page_title="Plataforma de Análisis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2️⃣ Importa la interfaz; al importarse, ui.py dibuja todo
from . import ui   # NO llamamos ui.render()

def main():
    # No hacemos nada aquí; mantener la función evita errores de Streamlit
    pass

if __name__ == "__main__":
    main()
