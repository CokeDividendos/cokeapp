import streamlit as st
from streamlit_authenticator.google_authenticator import GoogleAuthenticator

from .db import get_user, upsert_user


_authenticator = None


def _get_authenticator():
    global _authenticator
    if _authenticator is None:
        _authenticator = GoogleAuthenticator(
            name="Coke Dividendos App",
            client_id=st.secrets["google"]["client_id"],
            client_secret=st.secrets["google"]["client_secret"],
        )
    return _authenticator


def login_required() -> bool:
    """Show Google login button and return True if user authenticated."""
    authenticator = _get_authenticator()
    user = authenticator.login("Iniciar sesión")
    if user:
        # Ensure we have user record
        name = user.get("name")
        email = user.get("email")
        st.session_state["current_user"] = {"name": name, "email": email}
        if not get_user(email):
            upsert_user(email=email)
        return True
    return False


def current_user():
    return st.session_state.get("current_user")
