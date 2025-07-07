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

# src/auth.py  – dentro de login_required()

def login_required() -> bool:
    if "user" in st.session_state:
        return True

    # --- estilos -----------------------------------------------------------------
    st.markdown(
        """
        <style>
        /* cuerpo pantalla de login */
        div[data-testid="stAppViewContainer"] > .main {
            display:flex;
            align-items:center;
            justify-content:center;
        }
        /* tarjeta */
        .login-card {
            padding:2rem 3rem;
            background:#FFFFFF10;            /* semi-transparente sobre tema oscuro */
            border:1px solid #FFFFFF22;
            border-radius:12px;
            box-shadow:0 4px 15px rgba(0,0,0,.25);
            backdrop-filter:blur(6px);
            text-align:center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        st.markdown("### Accede con tu cuenta de Google")

        result = oauth2.authorize_button(
            "Iniciar sesión con Google",
            "https://cokeapp.streamlit.app",
            "openid email profile",
            key="google_login",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    if result and "token" in result:
        email = result["token"]["email"]
        upsert_user(email=email)
        st.session_state["user"] = get_user(email)
        return True

    st.stop()


# auth.py  ── dentro de login_required()  ─────────────────────────────

result = oauth2.authorize_button(
    "Iniciar sesión con Google",          # label
    "https://cokeapp.streamlit.app",      # redirect_uri  (la misma del constructor)
    "openid email profile",               # scope
    key="google_login",
)

def logout_button() -> None:
    """Botón de cierre de sesión en la barra lateral."""
    if "user" in st.session_state:
        if st.sidebar.button("Cerrar sesión"):
            st.session_state.clear()
            st.experimental_rerun()
