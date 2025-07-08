import streamlit as st
from src.auth import login_required, logout_button
from src.ui import render

def main():
    st.set_page_config(layout="wide")
    if login_required():
        with st.sidebar:
            st.write("Usuario actual:", st.session_state.get("user_email"))
            st.write("Nombre:", st.session_state.get("user_name"))
            logout_button()
        st.markdown(
            f"<h2>Bienvenido, {st.session_state.get('user_name','')}</h2>",
            unsafe_allow_html=True
        )
        render()

if __name__ == "__main__":
    main()
