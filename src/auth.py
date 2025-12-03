# src/auth.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
from .db import init_db, sqlite3, DB_PATH

init_db()

def login_required():
    """
    Gestiona el flujo de login con Google.
    - Muestra un botón de login si no hay código OAuth.
    - Procesa el código OAuth y actualiza la BD y session_state.
    - Permite múltiples usuarios sin arrastrar el estado del anterior.
    """
    # Limpia mensajes de error OAuth
    if "error" in st.query_params:
        st.query_params.clear()
        st.experimental_rerun()

    # Credenciales de Google desde secrets
    if "google" not in st.secrets:
        st.error("No se encontró la sección [google] en secrets.")
        st.stop()
    cfg = st.secrets["google"]
    for k in ("client_id", "client_secret", "redirect_uri"):
        if k not in cfg:
            st.error(f"Falta '{k}' en secrets.")
            st.stop()

    client_id = cfg["client_id"]
    client_secret = cfg["client_secret"]
    redirect_uri = cfg["redirect_uri"]
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ]

    params = st.query_params
    # Si hay código en la URL, procesa login aunque haya user en sesión (nuevo login)
    if "code" in params:
        code = params["code"]
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

        # Obtiene info del usuario desde Google
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        user_info = resp.json()
        email = user_info.get("email")
        nombre = user_info.get("name", "")

        # Actualiza BD: inserta o actualiza nombre
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE usuarios SET nombre = ? WHERE email = ?", (nombre, email))
        else:
            cur.execute("INSERT INTO usuarios (email, nombre) VALUES (?, ?)", (email, nombre))
        conn.commit()
        cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        # Reinicia completamente la session_state y guarda la nueva sesión
        st.session_state.clear()
        st.session_state["google_token"] = credentials.token
        st.session_state["user"] = email
        st.session_state["user_db"] = user

        # Limpia parámetros de la URL y recarga
        st.query_params.clear()
        st.experimental_rerun()
        return False

    # Si ya hay user en sesión y no hay código en la URL, no hay nada más que hacer
    if "user" in st.session_state and "user_db" in st.session_state:
        return True

    # Sin usuario ni código: muestra botón de login
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
        prompt="select_account",
        access_type="offline",
        include_granted_scopes="true",
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
        </div>""",
        unsafe_allow_html=True,
    )
    return False

def get_nombre_usuario():
    user = st.session_state.get("user_db")
    return user[2] if user and len(user) > 2 else ""

def get_tipo_plan():
    user = st.session_state.get("user_db")
    return user[3] if user and len(user) > 3 else ""

def logout_button():
    """Muestra botón 'Cerrar sesión' y limpia completamente la sesión."""
    if st.button("Cerrar sesión", key="logout_btn"):
        st.session_state.clear()
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.experimental_rerun()
