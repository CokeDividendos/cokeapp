import streamlit as st
from auth import login_required, logout_button

def main():
    st.set_page_config(layout="wide", page_title="Análisis Financiero y Portafolio de Dividendos")
    
    if login_required():
        st.sidebar.write("Bienvenido a tu panel de análisis financiero.")
        logout_button()
        # Aquí puedes agregar el resto de la UI de la aplicación
        st.write("¡Contenido de la aplicación (panel de inversión, análisis, etc.)!")
    else:
        st.write("Debes iniciar sesión para acceder al contenido de la aplicación.")

if __name__ == "__main__":
    main()
