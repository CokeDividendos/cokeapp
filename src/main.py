import streamlit as st
from auth import login_required, logout_button

def main():
    st.set_page_config(layout="wide")
    if login_required():
        st.sidebar.write("Usuario en sesión:", st.session_state.get("user"))
        st.sidebar.write("Registro DB:", st.session_state.get("user_db"))
        logout_button()
        st.title("Demo Multiusuario")
        st.write(f"Bienvenido, {st.session_state['user_db'][2]} ({st.session_state['user_db'][1]})")

if __name__ == "__main__":
    main()
