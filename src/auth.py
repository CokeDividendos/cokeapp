import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "cokeapp.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            nombre TEXT
        );
    """)
    conn.commit()
    conn.close()

def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()
    return user

init_db()

def login_required():
    # Si ya hay usuario en sesión, úsalo directamente
    if "user" in st.session_state and "user_db" in st.session_state:
        return True

    # Limpia parámetros de error OAuth
    if "error" in st.query_params:
        st.query_params.clear()
        st.experimental_rerun()

    # Configuración Google
    if "google" not in st.secrets:
        st.error("No se encontró la sección [google] en los secrets de Streamlit Cloud.")
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
        # Forzar selección de cuenta SIEMPRE
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

        # Info de Google
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        user_info = resp.json()
        email = user_info.get("email")
        nombre = user_info.get("name", "")

        # Guardar en DB si es nuevo
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

        # Actualiza SIEMPRE el estado de sesión
        st.session_state.clear()  # Esto borra TODO lo anterior
        st.session_state["user"] = email
        st.session_state["user_db"] = user
        st.query_params.clear()
        st.experimental_rerun()
    return True

def logout_button():
    if "user" in st.session_state:
        if st.button("Cerrar sesión", key="logout_btn"):
            st.session_state.clear()
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.experimental_rerun()
