# src/auth.py
import streamlit as st
from google_auth_oauthlib.flow import Flow
import requests
import datetime
from .db import init_db, upsert_user, get_user_by_email

# Asegura que la tabla de usuarios exista
init_db()

def _build_client_config(google_cfg: dict) -> dict:
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
    1) Si no hay [google] en secrets: error.
    2) Si no hay user_db en sesión: inicia OAuth o procesa el callback.
       - Muestra un botón naranja para iniciar sesión.
    3) Tras callback, guarda/actualiza usuario en BD y recarga.
    """
    if "google" not in st.secrets:
        st.error("❌ Falta la sección [google] en los Secrets de Streamlit.")
        st.stop()
    google_cfg = st.secrets["google"]
    for k in ("client_id", "client_secret", "redirect_uri"):
        if k not in google_cfg:
            st.error(f"❌ Falta '{k}' en tus Secrets bajo [google].")
            st.stop()

    client_config = _build_client_config(google_cfg)
    redirect = google_cfg["redirect_uri"]

    if "user_db" not in st.session_state:
        params = st.experimental_get_query_params()

        # 1) Sin código: pedir permiso
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

            # --- BOTÓN NARANJO PARA LOGIN ---
            st.markdown(
                f"""
                <div style="text-align:center; margin-top:4rem;">
                  <a
                    href="{auth_url}"
                    style="
                      display:inline-block;
                      background-color:#FF8800;
                      color:white;
                      padding:1rem 2rem;
                      border-radius:6px;
                      text-decoration:none;
                      font-weight:600;
                      font-size:1.1rem;
                    "
                  >
                    🔐 Iniciar sesión con Google
                  </a>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return False

        # 2) Con código: intercambiar token y obtener info
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
        name  = info.get("name", "")
        if not email:
            st.error("No se obtuvo correo del usuario.")
            st.stop()

        upsert_user(
            email=email,
            nombre=name,
            fecha_registro=datetime.datetime.now().isoformat(),
        )
        st.session_state["user_db"] = get_user_by_email(email)

        st.experimental_set_query_params()
        st.experimental_rerun()
        return False

    return True


def get_nombre_usuario() -> str | None:
    """Retorna el nombre para saludo."""
    u = st.session_state.get("user_db")
    return u[2] if (u and len(u) >= 3) else None


def get_tipo_plan() -> str:
    """Retorna el tipo de cuenta (free/premium/admin)."""
    u = st.session_state.get("user_db")
    return u[3] if (u and len(u) >= 4 and u[3]) else "free"


def logout_button():
    """
    Botón de Cerrar sesión con key único.
    Al pulsar, limpia la sesión y recarga.
    """
    if st.sidebar.button("🚪 Cerrar sesión", key="logout_btn"):
        st.session_state.clear()
        st.experimental_rerun()
