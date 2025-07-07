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

    if "google_token" in st.session_state and "user" in st.session_state:
        return True

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
        auth_url, _ = flow.authorization_url(
            prompt='consent',
            access_type='offline',
            include_granted_scopes='true'
        )
        st.markdown(
            f"""
            <div style="display:flex;justify-content:center;margin-top:64px">
              <a href="{auth_url}"><button style="font-size:1.2rem;padding:0.8em 2em">Iniciar sesión con Google</button></a>
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
