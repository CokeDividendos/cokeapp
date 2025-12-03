# src/services/yf_client.py
import os
import requests
import yfinance as yf
import tenacity
import pandas as pd
import streamlit as st
from .cache import install_cache, cache_data

# Configura caché HTTP (requests-cache) con expiración de 24 h
install_cache()

IS_CLOUD = os.getenv("STREAMLIT_CLOUD") == "1"
YF_SESSION = None

# Usa curl_cffi cuando está disponible (modo Chrome)
if not IS_CLOUD:
    try:
        from curl_cffi import requests as curl_requests
        _chrome = curl_requests.Session(impersonate="chrome")
        YF_SESSION = _chrome
        if hasattr(yf, "set_requests_session"):
            yf.set_requests_session(_chrome)
        st.info("🕸️ Usando sesión curl_cffi (modo Chrome)")
    except Exception as e:
        st.warning(f"No se cargó curl_cffi: {e}")

@tenacity.retry(
    stop=tenacity.stop_after_attempt(4),
    wait=tenacity.wait_exponential(multiplier=2, min=2, max=10),
    reraise=True,
)
def safe_history(ticker: str, *, period: str, interval: str) -> pd.DataFrame:
    """Invoca yfinance con reintentos y sesión personalizada."""
    return yf.Ticker(ticker, session=YF_SESSION).history(period=period, interval=interval)

@cache_data(show_spinner=False, ttl=60 * 60 * 24)
def history_resiliente(ticker: str, *, period: str, interval: str) -> pd.DataFrame:
    """
    Obtiene el historial de precios de un ticker de forma tolerante a fallos y lo almacena en caché.

    - Usa safe_history con reintentos exponenciales.
    - Si Yahoo devuelve 401, vuelve a intentar sin la sesión especial.
    - El decorador cache_data guarda los resultados durante 24 h para reducir llamadas.
    """
    try:
        return safe_history(ticker, period=period, interval=interval)
    except requests.exceptions.HTTPError as e:
        if getattr(e.response, "status_code", None) == 401:
            st.warning("⚠️ Yahoo devolvió 401; reintento sin sesión especial…")
            return yf.Ticker(ticker).history(period=period, interval=interval)
        raise

@cache_data(show_spinner=False, ttl=60 * 60 * 24)
def get_logo_url(info: dict) -> str | None:
    """Devuelve el logo de la empresa desde info['logo_url'] o vía Clearbit."""
    if logo := info.get("logo_url"):
        return logo
    domain = (info.get("website") or "").split("//")[-1].split("/")[0]
    if domain:
        return f"https://logo.clearbit.com/{domain}"
    return None

