import streamlit as st
from streamlit_oauth import OAuth2Component
from .db import get_user, upsert_user


# ── Credenciales OAuth2 guardadas en Secrets ──────────────────────────────────
CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]


# ── Componente de login con Google ────────────────────────────────────────────
import streamlit as st
from streamlit_oauth import OAuth2Component
from .db import get_user, upsert_user

CLIENT_ID = st.secrets["google"]["client_id"]
CLIENT_SECRET = st.secrets["google"]["client_secret"]

oauth2 = OAuth2Component(
    CLIENT_ID,
    CLIENT_SECRET,
    "https://accounts.google.com/o/oauth2/auth",   # authorize_url
    "https://oauth2.googleapis.com/token",        # token_url
    "https://cokeapp.streamlit.app",              # redirect_uri  (registrado en GCP)
    "openid email profile",                       # scope (string!)
)

# ── Helpers de sesión ─────────────────────────────────────────────────────────
def login_required() -> bool:
    """Muestra el botón Google hasta que el usuario esté autenticado."""
    if "user" in st.session_state:
        return True

    result = oauth2.authorize_button("Iniciar sesión con Google", key="google_login")
    if result and "token" in result:
        email = result["token"]["email"]
        upsert_user(email=email)                  # inserta si no existe
        st.session_state["user"] = get_user(email)
        return True

    st.stop()


def logout_button() -> None:
    """Botón de cierre de sesión en la barra lateral."""
    if "user" in st.session_state:
        if st.sidebar.button("Cerrar sesión"):
            st.session_state.clear()
            st.experimental_rerun()
