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

    # ── 1. estilos generales ───────────────────────────────────────────────
    st.markdown(
        """
        <style>
        /* centrar el contenido mientras no haya sesión */
        div[data-testid="stAppViewContainer"] > .main {
            display:flex;                  /* flexbox */
            align-items:center;            /* centra vertical */
            justify-content:center;        /* centra horizontal */
        }
        /* tarjeta */
        .login-card{
            width:320px;
            padding:2rem 2.5rem 2.2rem;
            border-radius:14px;
            background:rgba(255,255,255,0.06);
            border:1px solid rgba(255,255,255,0.15);
            box-shadow:0 6px 18px rgba(0,0,0,0.30);
            backdrop-filter:blur(8px);
            text-align:center;
        }
        .login-card img{
            width:56px;
            margin-bottom:0.8rem;
        }
        .login-card h4{
            font-weight:600;
            margin:0 0 1.4rem;
            font-size:1.05rem;
        }
        /* botón de Google tiene su propio iframe; reforzamos el ancho  */
        iframe[title="streamlit_oauth.authorize_button"]{
            min-width:260px!important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ── 2. maquetado ────────────────────────────────────────────────────────
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        # logo Google (SVG ligero incrustado)
        st.markdown(
            """
            <img src="https://upload.wikimedia.org/wikipedia/commons/4/4a/Logo_2013_Google.png" />
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<h4>Accede con tu cuenta Google</h4>", unsafe_allow_html=True)

        result = oauth2.authorize_button(
            "Iniciar sesión con Google",
            "https://cokeapp.streamlit.app",   # redirect_uri
            "openid email profile",            # scope
            key="google_login",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    # ── 3. si llega el token, se guarda usuario y se continúa ──────────────
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
