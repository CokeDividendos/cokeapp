# src/auth.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
from .db import init_db, sqlite3, DB_PATH
import datetime

init_db()

def esta_habilitado(user) -> bool:
    """
    Lógica de autorización:
    - user[3] es la columna `tipo_plan` (free, premium, admin).
    - user[5] es `fecha_expiracion` (puede ser None).
    Puedes ajustar esta función para solo permitir ciertos tipos o validar fechas.
    """
    if not user:
        return False
    tipo = user[3] or "free"
    fecha_expiracion = user[5]
    if fecha_expiracion:
        # Si tiene fecha de expiración, comprobar que no esté vencida
        try:
            expira = datetime.datetime.fromisoformat(fecha_expiracion)
            if expira < datetime.datetime.now():
                return False
        except Exception:
            pass
    return tipo in ("free", "premium", "admin")

def login_required():
    """Gestión del flujo de login con Google y control de acceso."""
    # Limpia parámetros de error OAuth
    if "error" in st.query_params:
        st.experimental_set_query_params()
        st.experimental_rerun()

    # Lee credenciales de Google
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

    # Procesar callback si hay código
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
        try:
            flow.fetch_token(code=code)
        except Exception:
            st.error("Hubo un problema al validar el código de Google. Intenta nuevamente.")
            # Limpiar params y volver
            st.experimental_set_query_params()
            st.stop()

        credentials = flow.credentials

        # Obtiene info del usuario desde Google
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
        if resp.status_code != 200:
            st.error("No se pudo obtener información de tu cuenta de Google.")
            st.experimental_set_query_params()
            st.stop()
        user_info = resp.json()
        email = user_info.get("email")
        nombre = user_info.get("name", "")

        # Busca al usuario en la BD (solo permite acceso si ya existe)
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        if not user:
            st.error("⚠️ Tu correo no está registrado o no tienes permiso para acceder.\n\n"
                     "Contacta al administrador para solicitar acceso.")
            # Limpiar query params para evitar reintentar el mismo código
            st.experimental_set_query_params()
            st.stop()

        # Actualiza el nombre en la BD por si cambió
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE usuarios SET nombre = ? WHERE email = ?", (nombre, email))
        conn.commit()
        cur.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        # Verifica que esté habilitado
        if not esta_habilitado(user):
            st.error("⚠️ Tu suscripción ha expirado o no tienes acceso.")
            st.experimental_set_query_params()
            st.stop()

        # Limpia la session_state y guarda los datos del nuevo usuario
        st.session_state.clear()
        st.session_state["google_token"] = credentials.token
        st.session_state["user"] = email
        st.session_state["user_db"] = user

        # Limpia los parámetros de la URL y recarga
        st.experimental_set_query_params()
        st.experimental_rerun()
        return False

    # Si ya hay usuario en sesión, lo devuelve
    if "user" in st.session_state and "user_db" in st.session_state:
        return True

    # No hay usuario ni código: mostrar botón de login
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
    """Muestra botón 'Cerrar sesión' y limpia sesión y URL."""
    if st.button("Cerrar sesión", key="logout_btn"):
        st.session_state.clear()
        # Limpia query params para no reutilizar el código anterior
        st.experimental_set_query_params()
        st.experimental_rerun()
