import streamlit as st
from streamlit_oauth import OAuth2Component
from .db import get_user, upsert_user

# ── Credenciales OAuth ─────────────────────────────────────────────────────────
_CLIENT_ID = st.secrets["google"]["client_id"]
_CLIENT_SECRET = st.secrets["google"]["client_secret"]

# ── Google OAuth2 end-points  ─────────────────────────────────────────────────
AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REDIRECT_URI = "https://cokeapp.streamlit.app"          # debe estar en Google Cloud

# ── Componente OAuth2  ────────────────────────────────────────────────────────
oauth2 = OAuth2Component(
    client_id=_CLIENT_ID,
    client_secret=_CLIENT_SECRET,
    authorize_url=AUTH_URL,          # nombre correcto
    token_url=TOKEN_URL,             # nombre correcto
    redirect_uri=REDIRECT_URI,       # la clase admite este parámetro
    scope="openid email profile",
)

# ── Helpers de sesión ─────────────────────────────────────────────────────────
def login_required() -> bool:
    """Muestra el botón Google hasta que el usuario se autentique."""
    if "user" in st.session_state:
        return True

    result = oauth2.authorize_button("Iniciar sesión con Google",
                                     key="google_login")
    if result and "token" in result:
        email = result["token"]["email"]
        upsert_user(email=email)
        st.session_state["user"] = get_user(email)
        return True

    st.stop()


def logout_button() -> None:
    """Renderiza un botón de cierre de sesión en el sidebar."""
    if "user" in st.session_state:
        if st.sidebar.button("Cerrar sesión"):
            st.session_state.clear()
            st.experimental_rerun()
