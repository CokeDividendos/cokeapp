import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests

def login_required():
    # Si ya hay usuario en sesión, úsalo directamente.
    if "user_email" in st.session_state and "user_name" in st.session_state:
        return True

    # Limpia parámetros de error OAuth de la URL
    if "error" in st.query_params:
        st.query_params.clear()
        st.experimental_rerun()

    # Configuración de Google OAuth
    if "google" not in st.secrets:
        st.error("Falta la sección [google] en los secrets.")
        st.stop()
    google_secrets = st.secrets["google"]
    client_id = google_secrets["client_id"]
    client_secret = google_secrets["client_secret"]
    redirect_uri = google_secrets["redirect_uri"]
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
    query_params = st.query_params

    if "code" not in query_params:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=scopes,
            redirect_uri=redirect_uri,
        )
        # Fuerza SIEMPRE selección de cuenta
        auth_url, _ = flow.authorization_url(
            prompt='select_account',
            access_type='offline',
            include_granted_scopes='true'
        )
        st.markdown(
            f"""<div style="display:flex;justify-content:center;margin-top:32px">
              <a href="{auth_url}">
                <button style="font-size:1.15rem;padding:0.85em 2.2em;background:#FF8800;color:#fff;border:none;border-radius:10px;font-family:'Inter',sans-serif;font-weight:600;box-shadow:0 2px 8px #ff880033;cursor:pointer;transition:background .14s;">
                    Iniciar sesión con Google
                </button>
              </a>
            </div>""", unsafe_allow_html=True,
        )
        st.stop()
    else:
        code = query_params["code"]
        if isinstance(code, list):
            code = code[0]
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uris": [redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=scopes,
            redirect_uri=redirect_uri,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Obtiene info de usuario desde Google
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"}
        )
        user_info = resp.json()
        email = user_info.get("email")
        nombre = user_info.get("name", "")

        # Limpia todo el st.session_state antes de asignar el nuevo usuario
        st.session_state.clear()
        st.session_state["user_email"] = email
        st.session_state["user_name"] = nombre
        st.query_params.clear()
        st.experimental_rerun()
    return True

def logout_button():
    if "user_email" in st.session_state:
        if st.button("Cerrar sesión", key="logout_btn"):
            st.session_state.clear()
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.experimental_rerun()
