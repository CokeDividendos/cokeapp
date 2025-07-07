import streamlit as st
from streamlit_oauth import OAuth2Component
from .db import get_user, upsert_user

_CLIENT_ID = st.secrets["google"]["client_id"]
_CLIENT_SECRET = st.secrets["google"]["client_secret"]

# Solo client_id y client_secret en el constructor
oauth2 = OAuth2Component(_CLIENT_ID, _CLIENT_SECRET)

def login_required() -> bool:
    """Return True once the user logs in with Google and has a Gmail account."""
    if "user" in st.session_state:
        return True

    st.markdown(
        """
        <style>
        .login-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-card {
            width: 340px;
            padding: 2.5rem 2rem;
            border-radius: 14px;
            background: rgba(255,255,255,0.97);
            border: 1px solid rgba(150,150,150,0.14);
            box-shadow: 0 6px 18px rgba(0,0,0,0.15);
            text-align: center;
            margin: 0 auto;
        }
        .login-card img {
            width: 64px;
            margin: 0 auto 1.2rem;
            display: block;
        }
        .login-card h4 {
            margin-bottom: 1.2rem;
        }
        </style>
        <div class="login-wrapper">
          <div class="login-card">
        """,
        unsafe_allow_html=True,
    )

    st.image(
        "https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg",
        width=64,
    )
    st.markdown("<h4>Accede con tu cuenta Gmail (@gmail.com)</h4>", unsafe_allow_html=True)
    result = oauth2.authorize_button(
        "Iniciar sesión con Google",
        authorize_url="https://accounts.google.com/o/oauth2/auth",
        token_url="https://oauth2.googleapis.com/token",
        redirect_url="https://cokeapp.streamlit.app",  # <- igual que en Google Cloud
        scope="https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile openid",
        key="google_login"
    )
    st.markdown("</div></div>", unsafe_allow_html=True)

    if result and "token" in result:
        email = result["token"].get("email")
        if not email:
            st.error("No se pudo obtener el correo electrónico. Por favor, intenta con otra cuenta de Google.")
            st.stop()
        if not email.endswith("@gmail.com"):
            st.error("Solo se permiten cuentas de Gmail (@gmail.com) para registrarse e ingresar.")
            st.stop()
        upsert_user(email=email)
        st.session_state["user"] = get_user(email)
        return True

    st.stop()
    
def logout_button() -> None:
    """Render a logout button in the sidebar."""
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()
