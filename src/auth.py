import streamlit as st
from streamlit_oauth import OAuth2Component
from .db import get_user, upsert_user

_CLIENT_ID = st.secrets["google"]["client_id"]
_CLIENT_SECRET = st.secrets["google"]["client_secret"]

oauth2 = OAuth2Component(
    _CLIENT_ID,
    _CLIENT_SECRET,
    "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid",
    redirect_uri="https://cokeapp.streamlit.app/",
    token_uri="https://oauth2.googleapis.com/token",
    authorization_uri="https://accounts.google.com/o/oauth2/auth",
)


def login_required() -> bool:
    """Show Google login button until the user authenticates."""
    if "user" in st.session_state:
        return True

    result = oauth2.authorize_button("Iniciar sesión con Google", key="google_login")
    if result and "token" in result:
        email = result["token"]["email"]
        upsert_user(email=email)
        st.session_state["user"] = get_user(email)
        return True

    st.stop()


def logout_button() -> None:
    """Render a logout button in the sidebar."""
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()
