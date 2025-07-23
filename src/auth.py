import os
import streamlit as st

def get_google_secrets():
    """
    Obtiene la configuración de Google OAuth.
    Primero intenta cargar la configuración desde st.secrets (útil para desarrollo local con secrets.toml).
    Si no se encuentra, utiliza las variables de entorno.
    """
    try:
        google_secrets = st.secrets["google"]
        # Verifica que existan todas las claves necesarias
        if (google_secrets.get("client_id") and 
            google_secrets.get("client_secret") and 
            google_secrets.get("redirect_uri")):
            return google_secrets
    except Exception:
        # Si falla, pasa a la siguiente opción
        pass

    # Fallback: cargar desde variables de entorno
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.environ.get("GOOGLE_REDIRECT_URI")
    
    if not (client_id and client_secret and redirect_uri):
        st.error("Error: La configuración de Google OAuth es necesaria. Por favor, define las variables de entorno o configura st.secrets correctamente.")
        return None
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }

def login_required():
    """
    Función que verifica si el usuario ha iniciado sesión.
    En caso negativo, muestra un botón para iniciar sesión (aquí se simula el flujo OAuth).
    """
    google_secrets = get_google_secrets()
    if google_secrets is None:
        return False

    # Verifica si ya existe una sesión iniciada mediante session_state
    if st.session_state.get("logged_in", False):
        return True

    st.write("Por favor, inicia sesión con Google para continuar.")
    if st.button("Iniciar sesión con Google"):
        # Aquí se debería implementar el flujo real de OAuth.
        # Por ahora, simulamos el login.
        st.session_state["logged_in"] = True
        st.success("Has iniciado sesión exitosamente.")
        return True

    return False

def logout_button():
    """
    Muestra un botón para cerrar sesión, limpiando la variable de sesión.
    """
    if st.button("Cerrar sesión"):
        st.session_state["logged_in"] = False
        st.success("Has cerrado sesión.")
