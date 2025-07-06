import streamlit as st

st.set_page_config(
    page_title="Plataforma de Análisis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ⬇️  Solo importamos; NO llamamos a ui.render()
from . import ui


def main():
    # El pass evita error si Streamlit ejecuta main()
    pass


if __name__ == "__main__":
    main()
