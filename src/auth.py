import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
import os
from src.db import init_db, get_user_by_email, sqlite3, DB_PATH

init_db()

def get_google_secrets():
    """
    Devuelve las credenciales de Google desde variables de entorno (Render) o st.secrets (local/Cloud).
    Requiere que existan: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI como variables env en Render.
    """
    keys = ("client_id", "client_secret", "redirect_uri")
    if "google" in st.secrets:
        google_secrets = st.secrets["google"]
        return {key: google_secrets[key] for key in keys}
    # Render: lee de variables de entorno
    return {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI"),
    }

def login_required():
    # Si ya hay usuario en sesión, úsalo directamente
    if "user" in st.session_state and "user_db" in st.session_state:
        return True

    # Limpia parámetros de error OAuth
    if "error" in st.query_params:
        st.query_params.clear()
        st.experimental_rerun()

    # Configuración Google
    google_secrets = get_google_secrets()
    for key in ("client_id", "client_secret", "redirect_uri"):
        if not google_secrets.get(key):
            st.error(f"Falta '{key}' en variables de entorno o secrets. Configura en Render (Environment) o en .streamlit/secrets.toml.")
            st.stop()
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
        # Forzar selección de cuenta SIEMPRE
        auth_url, _ = flow.authorization_url(
            prompt='select_account',
            access_type='offline',
            include_granted_scopes='true'
        )
        st.markdown(
            f"""<div style="display:flex;justify-content:center;margin-top:32px">
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
                    transition:background .14s;"
                    onmouseover="this.style.background='#de6a00';"
                    onmouseout="this.style.background='#FF8800';"
                >
                    <img src="https://www.svgrepo.com/show/475656/google-color.svg" width="24" style="vertical-align:middle;margin-right:10px;margin-bottom:4px">Iniciar sesión con Google
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

        # Info de Google
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        user_info = resp.json()
        email = user_info.get("email")
        nombre = user_info.get("name", "")

        # Debug temporal
        st.write(f"Email de Google: {email}, Nombre: {nombre}")

        # Siempre sincroniza el nombre desde Google, aunque el usuario ya exista
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        user = cur.fetchone()
        if not user:
            cur.execute("INSERT INTO usuarios (email, nombre) VALUES (?, ?)", (email, nombre))
            conn.commit()
            cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
            user = cur.fetchone()
        else:
            cur.execute("UPDATE usuarios SET nombre = ? WHERE email = ?", (nombre, email))
            conn.commit()
        conn.close()

        # Actualiza SIEMPRE el estado de sesión CON EL EMAIL DE GOOGLE
        st.session_state["google_token"] = credentials.token
        st.session_state["user"] = email
        st.session_state["user_db"] = user
        st.query_params.clear()
        st.experimental_rerun()
    return True

def get_nombre_usuario():
    user = st.session_state.get("user_db")
    return user[2] if user and len(user) > 2 else ""  # columna nombre

def get_tipo_plan():
    user = st.session_state.get("user_db")
    return user[3] if user and len(user) > 3 else ""

def logout_button():
    if "user" in st.session_state:
        if st.button("Cerrar sesión", key="logout_btn"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.experimental_rerun()
