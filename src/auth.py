import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests

def login_required():
    # Comprobación robusta de secrets
    if "google" not in st.secrets:
        st.error("No se encontró la sección [google] en los secrets de Streamlit Cloud.")
        st.stop()
    google_secrets = st.secrets["google"]
    for key in ("client_id", "client_secret", "redirect_uri"):
        if key not in google_secrets:
            st.error(f"Falta '{key}' en secrets. Por favor, revisa en Settings > Secrets de Streamlit Cloud.")
            st.stop()
    client_id = google_secrets["client_id"]
    client_secret = google_secrets["client_secret"]
    redirect_uri = google_secrets["redirect_uri"]
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email"
    ]

    # Ya está logueado
    if "google_token" in st.session_state and "user" in st.session_state:
        return True

    query_params = st.query_params
    if "code" not in query_params:
        # --- LOGIN UI PERSONALIZADO ---
        st.markdown(
            """
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
            <div style="text-align:center; margin-top:48px;">
                <img src="https://i.imgur.com/aznQh7O.png" width="96" style="border-radius:24px;box-shadow:0 2px 8px #ff880033;">
                <h2 style="color:#223354;font-family:'Inter',sans-serif;margin-top:16px;">Bienvenido a <span style="color:#FF8800;">CokeApp</span></h2>
                <p style="color:#6B778C;font-size:1.12em;margin-bottom:36px;">
                    Plataforma profesional para análisis financiero y seguimiento de inversiones.
                </p>
            </div>
            """, unsafe_allow_html=True
        )

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
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline',
            include_granted_scopes='true'
        )
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;margin-top:32px">
              <a href="{auth_url}">
                <button style="
                    font-size:1.15rem;
                    padding:0.85em 2.2em;
                    background:#FF8800;
                    color:#fff;
                    border:none;
                    border-radius:10px;
                    font-family:'Inter',sans-serif;
                    font-weight:600;
                    box-shadow:0 2px 8px #ff880033;
                    cursor:pointer;
                    transition:background .14s;
                " 
                onmouseover="this.style.background='#de6a00';"
                onmouseout="this.style.background='#FF8800';"
                >
                    <img src="https://www.svgrepo.com/show/475656/google-color.svg" width="24" style="vertical-align:middle;margin-right:10px;margin-bottom:4px">Iniciar sesión con Google
                </button>
              </a>
            </div>
            """,
            unsafe_allow_html=True,
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

        # Obtener datos usuario
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        user_info = resp.json()
        email = user_info.get("email")
        st.session_state["google_token"] = credentials.token
        st.session_state["user"] = email

        st.query_params.clear()
        st.experimental_rerun()

    return True

def logout_button():
    if "user" in st.session_state:
        if st.sidebar.button("Cerrar sesión"):
            st.session_state.clear()
            st.experimental_rerun()
