# src/auth.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
import datetime
from .db import init_db, upsert_user, get_user_by_email

# Asegura que la tabla exista
init_db()

def _build_client_config(google_cfg: dict) -> dict:
    """
    Construye el dict que Google espera:
    {
      "web": {
        "client_id": ...,
        "client_secret": ...,
        "auth_uri": ...,
        "token_uri": ...,
        "redirect_uris": [...],
      }
    }
    Rellena auth_uri/token_uri con valores por defecto si no están.
    """
    return {
        "web": {
            "client_id": google_cfg["client_id"],
            "client_secret": google_cfg["client_secret"],
            "auth_uri": google_cfg.get(
                "auth_uri", "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": google_cfg.get(
                "token_uri", "https://oauth2.googleapis.com/token"
            ),
            "redirect_uris": google_cfg.get(
                "redirect_uris", [google_cfg["redirect_uri"]]
            ),
        }
    }

def login_required() -> bool:
    """
    Gestiona OAuth2 con Google:
      1. Si no hay usuario en session_state, redirige a Google
      2. Procesa el callback, guarda/actualiza en BD y recarga.
      3. Retorna True si ya está logueado.
    """
    # 1) Revisar que exista sección [google] en Secrets
    if "google" not in st.secrets:
        st.error("❌ Falta la sección [google] en los Secrets de Streamlit.")
        st.stop()

    google_cfg = st.secrets["google"]
    for key in ("client_id", "client_secret", "redirect_uri"):
        if key not in google_cfg:
            st.error(f"❌ Falta '{key}' en tus Secrets bajo [google].")
            st.stop()

    # Construir la configuración completa para google_auth_oauthlib
    client_config = _build_client_config(google_cfg)
    redirect = google_cfg["redirect_uri"]

    # 2) Si no hay usuario en session, iniciar o procesar OAuth
    if "user_db" not in st.session_state:
        params = st.experimental_get_query_params()

        # 2a) Sin 'code': pedir autorización a Google
        if "code" not in params:
            flow = Flow.from_client_config(
                client_config,
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile",
                ],
                redirect_uri=redirect,
            )
            auth_url, state = flow.authorization_url(
                access_type="offline",
                include_granted_scopes="true",
                prompt="select_account",
            )
            st.session_state["oauth_state"] = state
            st.markdown(f"[🔐 Iniciar sesión con Google]({auth_url})")
            return False

        # 2b) Con 'code': intercambio y obtención de datos
        code = params["code"][0]
        flow = Flow.from_client_config(
            client_config,
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
            state=st.session_state.get("oauth_state"),
            redirect_uri=redirect,
        )
        flow.fetch_token(code=code)
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            params={"access_token": flow.credentials.token},
        )
        if resp.status_code != 200:
            st.error("Error obteniendo datos de usuario desde Google.")
            st.stop()

        info = resp.json()
        email = info.get("email")
        name = info.get("name") or ""
        if not email:
            st.error("No se obtuvo correo del usuario.")
            st.stop()

        # 3) Grabar o actualizar en BD
        upsert_user(
            email=email,
            nombre=name,
            fecha_registro=datetime.datetime.now().isoformat(),
        )
        st.session_state["user_db"] = get_user_by_email(email)

        # 4) Limpiar params y recargar
        st.experimental_set_query_params()
        st.experimental_rerun()
        return False

    # Ya hay sesión activa
    return True

def get_nombre_usuario() -> str | None:
    """Devuelve el nombre registrado en BD."""
    u = st.session_state.get("user_db")
    return u[2] if (u and len(u) >= 3) else None

def get_tipo_plan() -> str:
    """Devuelve el tipo de cuenta (free/premium/admin)."""
    u = st.session_state.get("user_db")
    return u[3] if (u and len(u) >= 4 and u[3]) else "free"

def logout_button():
    """Botón para limpiar sesión y recargar la app."""
    if st.sidebar.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.experimental_rerun()
