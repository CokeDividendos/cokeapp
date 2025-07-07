import streamlit as st
from streamlit_oauth import OAuth2Component
from .db import get_user, upsert_user

# ── Credenciales guardadas en Streamlit Secrets ───────────────────────────────
_CLIENT_ID = st.secrets["google"]["client_id"]
_CLIENT_SECRET = st.secrets["google"]["client_secret"]

# ── Configuración OAuth2 (“google” incluye internally los end-points) ─────────
oauth2 = OAuth2Component(
    client_id=_CLIENT_ID,
    client_secret=_CLIENT_SECRET,
    provider="google",                           # ← carga URIs de auth & token
    redirect_uri="https://cokeapp.streamlit.app",
    scopes=("openid", "email", "profile"),
)

# ── Login y logout helpers ────────────────────────────────────────────────────
def login_required() -> bool:
    """Muestra el botón de login hasta que el usuario se autentique."""
    if "user" in st.session_state:
        return True

    result = oauth2.authorize_button("Iniciar sesión con Google", key="google_login")
    if result and "token" in result:
        email = result["token"]["email"]
        upsert_user(email=email)                 # crea o actualiza registro
        st.session_state["user"] = get_user(email)
        return True

    st.stop()

def logout_button() -> None:
    """Botón de cierre de sesión en el sidebar."""
    if "user" in st.session_state:
        if st.sidebar.button("Cerrar sesión"):
            st.session_state.clear()
            st.experimental_rerun()
