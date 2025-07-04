from datetime import timedelta
import streamlit as st
import requests_cache


def install_cache():
    """Configure requests_cache with sensible defaults."""
    requests_cache.install_cache(
        "yf_cache",
        expire_after=timedelta(hours=24),
        allowable_codes=(200, 203, 300, 301, 404, 429),
        allowable_methods=("GET", "POST"),
    )


# Reexport Streamlit's cache_data decorator
cache_data = st.cache_data
