# auth.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
import datetime
from .db import init_db, upsert_user, get_user_by_email

# Asegurarse de crear tablas al arrancar
init_db()

def login_required() -> bool:
    """
    Si el usuario no está en sesión, inicia OAuth con Google.
    Al completar, sube/actualiza el registro en BD y guarda en session_state.
    """
    # 1. Validar secretos de Google
    if "google" not in st.secrets:
        st.error("Falta la sección [google] en los Secrets de Streamlit Cloud.")
        st.stop()
    google_cfg = st.secrets["google"]
    for k in ("client_id", "client_secret", "redirect_uri"):
        if k not in google_cfg:
            st.error(f"Falta '{k}' en los Secrets.")
            st.stop()

    # 2. Si no hay usuario en sesión, gestionar OAuth flow
    if "user_db" not in st.session_state:
        params = st.experimental_get_query_params()
        # 2a. Paso 1: redirigir a Google si no hay 'code'
        if "code" not in params:
            flow = Flow.from_client_config(
                {"web": google_cfg},
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                ],
                redirect_uri=google_cfg["redirect_uri"],
            )
            auth_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="select_account"
            )
            st.session_state["oauth_state"] = state
            st.markdown(f"[➤ Iniciar sesión con Google]({auth_url})")
            return False
        # 2b. Paso 2: procesar callback con código
        code = params["code"][0]
        flow = Flow.from_client_config(
            {"web": google_cfg},
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
            state=st.session_state.get("oauth_state"),
            redirect_uri=google_cfg["redirect_uri"],
        )
        flow.fetch_token(code=code)
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            params={"access_token": flow.credentials.token},
        )
        if resp.status_code != 200:
            st.error("Error obteniendo datos de usuario.")
            st.stop()
        info = resp.json()
        email = info.get("email")
        name  = info.get("name")
        if not email:
            st.error("No se obtuvo correo del usuario.")
            st.stop()

        # 3. Registrar / actualizar en BD y en sesión
        upsert_user(
            email,
            nombre=name,
            fecha_registro=datetime.datetime.now().isoformat()
        )
        st.session_state["user_db"] = get_user_by_email(email)

        # 4. Limpiar params y recargar para que ya entre como ‘logged in’
        st.experimental_set_query_params()
        st.experimental_rerun()
        return False

    # Ya está logueado
    return True


def get_nombre_usuario() -> str | None:
    """Devuelve el nombre del usuario para mostrar en pantalla."""
    u = st.session_state.get("user_db")
    # la tupla es (id, email, nombre, tipo_plan, api_key, fecha_expiracion, fecha_registro)
    if u and len(u) >= 3:
        return u[2]
    return None


def get_tipo_plan() -> str:
    """Devuelve el tipo de cuenta (free/premium/admin)."""
    u = st.session_state.get("user_db")
    if u and len(u) >= 4 and u[3]:
        return u[3]
    return "free"


def logout_button():
    """Botón que limpia la sesión y recarga la app."""
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()
