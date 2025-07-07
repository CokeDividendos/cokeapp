import streamlit as st
import streamlit_authenticator as stauth
import yaml

def load_config():
    with open("config.yaml") as file:
        return yaml.safe_load(file)

def login_required():
    config = load_config()
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized'],
        oauth_config=config.get('oauth')
    )
    name, authentication_status, username = authenticator.login("Iniciar sesión", "main")
    if authentication_status:
        st.session_state["user"] = username
        return True
    elif authentication_status is False:
        st.error("No tienes acceso autorizado o tu correo no está permitido.")
        st.stop()
    else:
        st.warning("Por favor, inicia sesión")
        st.stop()

def logout_button():
    if "user" in st.session_state:
        if st.sidebar.button("Cerrar sesión"):
            del st.session_state["user"]
            st.experimental_rerun()
