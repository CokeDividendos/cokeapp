# src/auth.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
import datetime
from .db import init_db, upsert_user, get_user_by_email

# Asegúrate de que la tabla de usuarios exista
init_db()

def login_required() -> bool:
    """
    Gestiona el flujo OAuth de Google. 
    - Si el usuario no está en sesión, inicia OAuth y se detiene.
    - Tras el callback, inserta/actualiza el usuario en BD y recarga.
    """
    # 1. Validar configuración de Google en los Secrets
    if "google" not in st.secrets:
        st.error("Falta la sección [google] en los Secrets de Streamlit Cloud.")
        st.stop()
    google_cfg = st.secrets["google"]
    for key in ("client_id", "client_secret", "redirect_uri"):
        if key not in google_cfg:
            st.error(f"Falta '{key}' en los Secrets.")
            st.stop()

    # 2. Si no hay usuario en sesión, iniciar o procesar OAuth
    if "user_db" not in st.session_state:
        params = st.experimental_get_query_params()

        # 2a. Sin código: redirigir a Google
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
                prompt="select_account",
            )
            st.session_state["oauth_state"] = state
            st.markdown(f"[➤ Iniciar sesión con Google]({auth_url})")
            return False

        # 2b. Con código: intercambiar por token y obtener userinfo
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

        # 3. Insertar o actualizar usuario en la BD
        upsert_user(
            email=email,
            nombre=name,
            fecha_registro=datetime.datetime.now().isoformat(),
        )
        st.session_state["user_db"] = get_user_by_email(email)

        # 4. Limpiar params y recargar para entrar ya logueado
        st.experimental_set_query_params()
        st.experimental_rerun()
        return False

    # Si ya está en sesión, continuar
    return True

def get_nombre_usuario() -> str | None:
    """Retorna el nombre del usuario (campo 'nombre' de la BD)."""
    u = st.session_state.get("user_db")
    return u[2] if (u and len(u) >= 3) else None

def get_tipo_plan() -> str:
    """Retorna el campo 'tipo_plan' de la BD (free/premium/admin)."""
    u = st.session_state.get("user_db")
    return u[3] if (u and len(u) >= 4 and u[3]) else "free"

def logout_button():
    """Botón de cierre de sesión que limpia toda la session_state."""
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()
