# ╔═════════════  Coke-App v0.4  (logo, sector/industria, resumen-IA, UI móvil) ═════════════╗
# 1) IMPORTS & CONFIG  ───────────────────────────────────────────────────────────────────────
import os, datetime, requests, textwrap
from pathlib import Path
from datetime import timedelta

import streamlit as st          #  ← SIEMPRE el primer import de tu app
import pandas as pd, plotly.graph_objects as go, plotly.express as px, numpy as np
import yfinance as yf, requests_cache, tenacity

# ───── 1-A  page config (¡debe ser la PRIMERA llamada st.*!) ────────────────────────────────
st.set_page_config(
    page_title="Plataforma de Análisis",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ───── 1-B  CSS responsive minimal (look Fintual) ───────────────────────────────────────────
st.markdown(
    """
    <style>
    html, body, [class*="css"]{font-family:"Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
    @media (max-width:750px){
        .main .block-container{padding:1rem .5rem}
        .element-container{width:100%!important}
        h1,h2{font-size:1.2rem}
    }
    /* Hace redondo cualquier logo descargado */
    img[src*="logo.clearbit.com"], img[src$=".png"]{
        border-radius:50%;
        background:#fff;
        padding:4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ╔═════════════ 2) “INFRAESTRUCTURA”: CACHE HTTP + SESIÓN YF  ═══════════════════════════════
requests_cache.install_cache(
    "yf_cache",
    expire_after=timedelta(hours=24),
    allowable_codes=(200, 203, 300, 301, 404, 429),
    allowable_methods=("GET", "POST"),
)

IS_CLOUD   = os.getenv("STREAMLIT_CLOUD") == "1"
YF_SESSION = None

# — Solo usamos curl_cffi cuando NO estamos en la nube ————————————————
if not IS_CLOUD:
    try:
        from curl_cffi import requests as curl_requests          # pip install curl-cffi
        _chrome = curl_requests.Session(impersonate="chrome")
        YF_SESSION = _chrome
        if hasattr(yf, "set_requests_session"):
            yf.set_requests_session(_chrome)
        st.info("🕸️ Usando sesión curl_cffi (modo Chrome)")
    except Exception as e:
        st.warning(f"No se cargó curl_cffi: {e}")

# ───── Funciones de descarga resiliente ────────────────────────────────
@tenacity.retry(
    stop=tenacity.stop_after_attempt(4),
    wait=tenacity.wait_exponential(multiplier=2, min=2, max=10),
    reraise=True,
)
def safe_history(ticker: str, *, period: str, interval: str) -> pd.DataFrame:
    """Descarga .history() con reintentos usando la sesión elegida."""
    return yf.Ticker(ticker, session=YF_SESSION).history(
        period=period, interval=interval
    )

def history_resiliente(ticker: str, *, period: str, interval: str) -> pd.DataFrame:
    """
    Llama a safe_history().  
    Si Yahoo devuelve 401 (sesión invalidada) reintenta inmediatamente con la
    sesión estándar de yfinance.
    """
    try:
        return safe_history(ticker, period=period, interval=interval)
    except requests.exceptions.HTTPError as e:
        if getattr(e.response, "status_code", None) == 401:
            st.warning("⚠️ Yahoo devolvió 401; reintento sin sesión especial…")
            return yf.Ticker(ticker).history(period=period, interval=interval)
        # para cualquier otro código de error, propaga la excepción
        raise

# ╔═════════════ 3) HELPERS  (logo y resumen IA) ═════════════════════════════════════════════
@st.cache_data(show_spinner=False, ttl=60*60*24)
def get_logo_url(info:dict)->str|None:
    """Devuelve un logo PNG. 1️⃣ Yahoo → 2️⃣ Clearbit → None"""
    if (logo:=info.get("logo_url")):           # algunos tickers lo traen
        return logo
    domain = (info.get("website") or "").split("//")[-1].split("/")[0]
    if domain:
        return f"https://logo.clearbit.com/{domain}"
    return None

@st.cache_data(show_spinner="💬 Traduciendo y resumiendo…", ttl=60*60*24)
def resumen_es(short_desc_en:str)->str:
    """Resumen en español usando OpenAI (requiere OPENAI_API_KEY en Secrets)."""
    try:
        import openai, os          # sólo si el usuario puso su clave
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        prompt = textwrap.dedent(f"""
            Resume al español en máximo 120 palabras, tono divulgativo,
            el siguiente texto EXPLICANDO qué hace la empresa.\n\n{short_desc_en}
        """)
        rsp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}],
            max_tokens=180,
            temperature=0.5,
        )
        return rsp.choices[0].message.content.strip()
    except Exception:
        return "Resumen no disponible"

# ╔═════════════ 4) IU PRINCIPAL  ════════════════════════════════════════════════════════════
# Tabs de alto nivel
tabs = st.tabs([
    "Valoración y Análisis Financiero",
    "Seguimiento de Cartera",
    "Analizar ETF's",
    "Finanzas Personales",
    "Calculadora de Interés Compuesto",
])
# ─── Tab 0 ───────────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    ########################  ENTRADAS  ######################################################
    col_logo, col_title = st.columns([1, 5])
    ticker_input = st.text_input("🔎 Ticker (ej.: AAPL, MSFT, KO)", "AAPL")

    period_dict   = {"5 años":"5y","10 años":"10y","15 años":"15y","20 años":"20y"}
    period_label  = st.selectbox("⏳ Período",   list(period_dict))   # lo que ve el usuario
    selected_period = period_dict[period_label]                      # la clave que usa YF

    interval_dict = {"Diario":"1d","Mensual":"1mo"}
    interval_label = st.selectbox("📆 Frecuencia", list(interval_dict))
    selected_interval = interval_dict[interval_label]

    ########################  DESCARGA YF  #####################################################
    try:
        ticker_data = yf.Ticker(ticker_input, session=YF_SESSION)

        # ⬇️ 1️⃣  CREA info ANTES de usarlo
        info = ticker_data.info or {}

        price_data = safe_history(
            ticker_input,
            period   = selected_period,
            interval = selected_interval,
        )

        if price_data.empty:
            st.warning("No se encontraron datos para ese ticker.")
            st.stop()

        ########################  LOGO + TÍTULO ###############################################
        logo_url = get_logo_url(info)
        with col_logo:
            if logo_url: st.image(logo_url, width=90)
        with col_title:
            st.title(f" {info.get('longName', ticker_input)}")
            # sector / industria justo bajo el título
            st.markdown(f"**🏷️ Sector:** {info.get('sector','N/D')}   |   **🏭 Industria:** {info.get('industry','N/D')}")

        ########################  RESUMEN BREVE IA  ###########################################
        if info.get("longBusinessSummary"):
            st.write(resumen_es(info["longBusinessSummary"]))

        # A partir de aquí TODO tu código de métricas, gráficos, etc. permanece igual
        #  (no lo repito para ahorrar espacio — no lo borres en tu archivo)
        # ----------------------------------------------------------------------------------

        # ……………………………………………………………………………………………………………………………………
        # 👇  PEGAR AQUÍ el resto de tu lógica (BLOQUES 1-6) tal cual la tenías
        # ……………………………………………………………………………………………………………………………………
    
        # ==========================
        # BLOQUE 1: Información General y Datos Clave (Cálculos Básicos)
        # ==========================
        primary_orange = "darkorange"
        primary_blue   = "deepskyblue"
        primary_pink   = "hotpink"

        info = ticker_data.info

        # ─── Conversión segura a numérico ───────────────────────────
        price        = pd.to_numeric(info.get('currentPrice'),  errors='coerce')
        dividend     = pd.to_numeric(info.get('dividendRate'),  errors='coerce')
        payout_ratio = pd.to_numeric(info.get('payoutRatio'),   errors='coerce')
        pe_ratio     = pd.to_numeric(info.get('trailingPE'),    errors='coerce')
        roe_actual   = pd.to_numeric(info.get('returnOnEquity'),errors='coerce')
        eps_actual   = pd.to_numeric(info.get('trailingEps'),   errors='coerce')
        pb           = pd.to_numeric(info.get('priceToBook'),   errors='coerce')

        yield_actual = (dividend / price * 100) if pd.notna(dividend) and pd.notna(price) else None

        # ─── Book Value / Share ─────────────────────────────────────
        bs = ticker_data.balance_sheet.transpose()
        capital_total = (bs.get("Total Equity Gross Minority Interest")
                        .iloc[0] if "Total Equity Gross Minority Interest" in bs else None)
        capital_total = pd.to_numeric(capital_total, errors='coerce')

        ordinary_shares = pd.to_numeric(info.get('sharesOutstanding'), errors='coerce')
        preferred_shares = 0   # asumimos 0 si no hay dato

        book_per_share = ((capital_total - preferred_shares) / ordinary_shares
                        if pd.notna(capital_total) and pd.notna(ordinary_shares) and ordinary_shares!=0
                        else None)

        # ─── Crecimiento esperado y múltiplos ───────────────────────
        G         = roe_actual * (1 - payout_ratio) if pd.notna(roe_actual) and pd.notna(payout_ratio) else None
        G_percent = G * 100 if pd.notna(G) else None

        if pd.notna(G_percent):
            multiplier = 10 if G_percent <= 10 else 15 if G_percent <= 20 else 20
        else:
            multiplier = None

        eps_5y      = eps_actual * ((1 + G_percent/100)**5) if pd.notna(eps_actual) and pd.notna(G_percent) else None
        per_5y      = eps_5y * multiplier if pd.notna(eps_5y) and multiplier else None
        g_esperado  = ((per_5y / price)**(1/5) - 1) if pd.notna(per_5y) and pd.notna(price) and price!=0 else None
        g_esperado_percent = g_esperado * 100 if pd.notna(g_esperado) else None
        fair_price  = pb * book_per_share if pd.notna(pb) and pd.notna(book_per_share) else None

        # ─── CAGR del dividendo ─────────────────────────────────────
        dividends = ticker_data.dividends
        if not dividends.empty:
            annual_dividends = (dividends.resample('Y').sum()
                                        .astype(float)
                                        .dropna())
            annual_dividends.index = annual_dividends.index.year
            start_year, end_year = price_data.index[[0,-1]].year
            annual_dividends = annual_dividends.loc[start_year:end_year]

            if len(annual_dividends) >= 3:
                first, penultimate = annual_dividends.iloc[[0,-2]]
                n_years            = annual_dividends.index[-2] - annual_dividends.index[0]
                cagr_dividend      = ( (penultimate/first)**(1/n_years) - 1 ) * 100
            else:
                cagr_dividend = None

            df_yield = price_data[['Close']].assign(
                Año            = price_data.index.year,
                Dividendo_Anual= price_data.index.year.map(annual_dividends.to_dict())
            )
            df_yield['Yield (%)'] = (df_yield['Dividendo_Anual']/df_yield['Close'])*100
            avg_yield = df_yield['Yield (%)'].mean()
        else:
            cagr_dividend = avg_yield = None

        # ─── Retornos históricos ────────────────────────────────────
        first_close  = price_data['Close'].iloc[0]
        last_close   = price_data['Close'].iloc[-1]
        total_return = (last_close/first_close - 1)*100
        years_span   = (price_data.index[-1] - price_data.index[0]).days / 365.25
        annual_return= ((last_close/first_close)**(1/years_span) - 1)*100 if years_span>0 else None

        # ─── Métricas en cabecera ───────────────────────────────────
        st.markdown(f"### 🚨 Datos Principales de {ticker_input}")
        col1,col2,col3,col4,col5,col6,col7 = st.columns(7)
        col1.metric("💰 Precio",     f"${price:.2f}"        if pd.notna(price)        else "N/D")
        col2.metric("🏦 Dividendo",  f"${dividend:.2f}"     if pd.notna(dividend)     else "N/D")
        col3.metric("📈 Yield",      f"{yield_actual:.2f}%" if pd.notna(yield_actual) else "N/D")
        col4.metric("📊 PER",        f"{pe_ratio:.2f}x"     if pd.notna(pe_ratio)     else "N/D")
        col5.metric("🔁 Pay-out",    f"{payout_ratio*100:.2f}%" if pd.notna(payout_ratio) else "N/D")
        col6.metric("🧾 EPS",        f"${eps_actual:.2f}"   if pd.notna(eps_actual)   else "N/D")
        col7.metric("⏳ CAGR div",   f"{cagr_dividend:.2f}%"if pd.notna(cagr_dividend)else "N/D")

        # ─── Precio histórico + Drawdown ────────────────────────────
        st.subheader("##")
        st.subheader("📈 Precio Histórico de la Acción")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=price_data.index, y=price_data['Close'],
            mode='lines',
            name='Close', line=dict(color=primary_blue)
        ))
        fig.update_layout(
            title=f'Precio de la acción ({period_label}, {interval_label.lower()})',
            xaxis_title='Fecha', yaxis_title='USD', height=500
        )
        st.plotly_chart(fig, use_container_width=True, key="price_history")

        st.subheader("⚠️ Drawdown Histórico")
        try:
            running_max = price_data['Close'].cummax()
            drawdown    = (price_data['Close']/running_max - 1)*100
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=drawdown.index, y=drawdown,
                mode='lines', name='Drawdown (%)',
                line=dict(color='crimson')
            ))
            fig_dd.update_layout(
                yaxis_title='Drawdown (%)',
                yaxis=dict(range=[drawdown.min()-5, 5]),
                height=450, margin=dict(l=30,r=30,t=60,b=30)
            )
            st.plotly_chart(fig_dd, use_container_width=True)
        except Exception as e:
            st.warning(f"No se pudo calcular el drawdown: {e}")


        # ==========================
        # BLOQUE 2: Valoración por Dividendo
        # ==========================
        st.subheader(f"🧐 Análisis y Valoración para {ticker_input}")

        with st.expander(f"💸 Análisis y Valoración por Dividendo de {ticker_input}"):
            # ---------- 2-A  Histórico anual de dividendos + CAGR ----------
            dividends = ticker_data.dividends
            if not dividends.empty:
                annual_dividends = (dividends.resample('Y').sum()      # serie
                                        .astype(float)              # aseguramos numérico
                                        .dropna())
                annual_dividends.index = annual_dividends.index.year

                start_year, end_year = price_data.index[[0, -1]].year
                annual_dividends = annual_dividends.loc[start_year:end_year]

                if len(annual_dividends) >= 3:
                    first, penultimate = annual_dividends.iloc[[0, -2]]
                    n_years = annual_dividends.index[-2] - annual_dividends.index[0]
                    cagr = ((penultimate / first) ** (1 / n_years) - 1) * 100
                    cagr_text = f"📌 CAGR {cagr:.2f}% anual ({annual_dividends.index[0]}–{annual_dividends.index[-2]})"
                else:
                    cagr_text = "📌 CAGR no disponible (datos insuf.)"

                fig_div = go.Figure()
                fig_div.add_trace(go.Bar(
                    x=annual_dividends.index,
                    y=annual_dividends.values,
                    name='Dividendo Anual ($)',
                    marker_color=primary_orange,
                    text=[f"${v:.2f}" for v in annual_dividends.values],
                    textposition='outside'
                ))
                fig_div.update_layout(
                    title=cagr_text, xaxis_title='Año', yaxis_title='Dividendo ($)',
                    height=450, margin=dict(l=30, r=30, t=60, b=30)
                )
                st.plotly_chart(fig_div, use_container_width=True, key="plotly_chart_div")

                st.markdown("#### Resumen de Dividendos por Año")
                st.table(pd.DataFrame(
                    {y: f"${annual_dividends.loc[y]:.2f}" for y in annual_dividends.index},
                    index=["Dividendo ($)"]
                ))

            # ---------- 2-B  Sostenibilidad del dividendo ----------
            st.subheader("♻️ Sostenibilidad del Dividendo")
            try:
                cashflow = ticker_data.cashflow.transpose()
                cashflow.index = cashflow.index.year

                fcf_col, dividends_col = "Free Cash Flow", "Cash Dividends Paid"
                if fcf_col in cashflow and dividends_col in cashflow:
                    fcf            = pd.to_numeric(cashflow[fcf_col],         errors="coerce")
                    dividends_paid = pd.to_numeric(cashflow[dividends_col],   errors="coerce")

                    df_fcf = (pd.DataFrame({
                                "FCF": fcf,
                                "Dividendos Pagados": dividends_paid.abs()
                            })
                            .dropna())
                    df_fcf["FCF Payout (%)"] = (df_fcf["Dividendos Pagados"] / df_fcf["FCF"]) * 100

                    fig_sost = go.Figure()
                    fig_sost.add_trace(go.Bar(x=df_fcf.index, y=df_fcf["FCF"],
                                            name="FCF", marker_color=primary_orange,
                                            text=df_fcf["FCF"].round(0), textposition="outside"))
                    fig_sost.add_trace(go.Bar(x=df_fcf.index, y=df_fcf["Dividendos Pagados"],
                                            name="Dividendos Pagados", marker_color=primary_blue,
                                            text=df_fcf["Dividendos Pagados"].round(0), textposition="outside"))
                    fig_sost.add_trace(go.Scatter(x=df_fcf.index, y=df_fcf["FCF Payout (%)"],
                                                name="FCF Payout (%)", mode="lines+markers+text",
                                                yaxis="y2", line=dict(color=primary_pink),
                                                text=[f"{v:.0f}%" for v in df_fcf["FCF Payout (%)"]],
                                                textposition="top right"))
                    fig_sost.update_layout(
                        title="FCF vs Dividendos Pagados y FCF Payout Ratio",
                        xaxis_title="Año", yaxis_title="Millones USD",
                        yaxis2=dict(title="FCF Payout (%)", overlaying="y", side="right"),
                        barmode="group", height=500, margin=dict(l=30, r=30, t=60, b=30)
                    )
                    st.plotly_chart(fig_sost, use_container_width=True, key="plotly_chart_sost")
                else:
                    st.warning("No se encontraron columnas de FCF o Dividendos en el cash-flow.")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de sostenibilidad: {e}")

            # ---------- 2-C  Rentabilidad histórica ----------
            st.subheader("📉 Rentabilidad por Dividendo Histórica")
            try:
                df_yield = price_data[["Close"]].copy()
                df_yield["Año"] = df_yield.index.year
                dividend_map = annual_dividends.to_dict() if not dividends.empty else {}
                df_yield["Dividendo Anual"] = (df_yield["Año"].map(dividend_map)
                                                            .astype(float))
                df_yield["Yield (%)"] = (df_yield["Dividendo Anual"] / df_yield["Close"]) * 100
                if len(annual_dividends) > 1:
                    max_full_year = annual_dividends.index[-2]
                    df_yield = df_yield[df_yield["Año"] <= max_full_year]

                avg_yield_div = df_yield["Yield (%)"].mean()
                max_yield_div = df_yield["Yield (%)"].max()
                min_yield_div = df_yield["Yield (%)"].min()

                fig_yield = go.Figure()
                fig_yield.add_trace(go.Scatter(
                    x=df_yield.index, y=df_yield["Yield (%)"],
                    mode="lines", name="Yield Diario",
                    line=dict(color=primary_pink)
                ))
                fig_yield.add_hline(y=avg_yield_div, line=dict(dash="dash"),
                                    annotation_text="Promedio")
                fig_yield.add_hline(y=max_yield_div, line=dict(dash="dot"),
                                    annotation_text="Máximo")
                fig_yield.add_hline(y=min_yield_div, line=dict(dash="dot"),
                                    annotation_text="Mínimo")
                fig_yield.update_layout(
                    title="Rentabilidad por Dividendo (filtrada)",
                    xaxis_title="Fecha", yaxis_title="Yield (%)",
                    height=450, margin=dict(l=30,r=30,t=60,b=30)
                )
                st.plotly_chart(fig_yield, use_container_width=True, key="plotly_chart_yield")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de yield: {e}")

            # ---------- 2-D  Método Geraldine Weiss ----------
            st.subheader(f"💎 Método Geraldine Weiss: Datos, Resumen y Gráfico")
            try:
                dividends = ticker_data.dividends
                price_data_diario = ticker_data.history(period=selected_period, interval="1d")
                if dividends.empty or price_data_diario.empty:
                    st.warning("No hay datos suficientes para calcular el Método Geraldine Weiss.")
                else:
                    annual_dividends_raw = dividends.resample("Y").sum()
                    annual_dividends_raw.index = annual_dividends_raw.index.year
                    start_year = pd.to_datetime(price_data.index[0]).year
                    end_year = pd.to_datetime(price_data.index[-1]).year
                    annual_dividends = annual_dividends_raw[(annual_dividends_raw.index >= start_year) & (annual_dividends_raw.index <= end_year)]
                    if len(annual_dividends) >= 3:
                        first_value = annual_dividends.iloc[0]
                        penultimate_value = annual_dividends.iloc[-2]
                        n_years = annual_dividends.index[-2] - annual_dividends.index[0]
                        cagr_gw = ((penultimate_value / first_value) ** (1 / n_years) - 1) * 100
                    else:
                        cagr_gw = None
                    current_year = pd.Timestamp.today().year
                    def ajustar_dividendo(year):
                        if (year == current_year) and (cagr_gw is not None) and ((year - 1) in annual_dividends.index):
                            return annual_dividends[year - 1] * (1 + cagr_gw/100)
                        else:
                            return annual_dividends.get(year, None)
                    
                    monthly_data = price_data_diario.resample("M").last().reset_index()
                    monthly_data['Año'] = monthly_data['Date'].dt.year
                    monthly_data['Mes'] = monthly_data['Date'].dt.strftime("%B")
                    monthly_data.rename(columns={'Close': 'Precio'}, inplace=True)
                    monthly_data['Dividendo Anual'] = monthly_data['Año'].apply(ajustar_dividendo)
                    monthly_data['Yield'] = monthly_data['Dividendo Anual'] / monthly_data['Precio']
                    overall_yield_min = monthly_data['Yield'].min()
                    overall_yield_max = monthly_data['Yield'].max()
                    monthly_data['Precio Sobrevalorado'] = monthly_data['Dividendo Anual'] / overall_yield_min
                    monthly_data['Precio Infravalorado'] = monthly_data['Dividendo Anual'] / overall_yield_max
                    monthly_data = monthly_data.sort_values(by='Date')
                    valor_infravalorado = monthly_data.iloc[-1]['Precio Infravalorado']
                    df_tabla = monthly_data[['Año', 'Mes', 'Precio', 'Dividendo Anual', 'Yield', 'Precio Sobrevalorado', 'Precio Infravalorado']]
                    ultimo_año = df_tabla['Año'].max()
                    last_dividend = df_tabla[df_tabla['Año'] == ultimo_año]['Dividendo Anual'].iloc[-1]
                    current_price_gw = ticker_data.info.get('currentPrice', price_data_diario['Close'].iloc[-1])
                    st.markdown("### 🚨 Datos Clave")
                    gw_cols = st.columns(7)
                    gw_cols[0].metric("💰 Precio Actual", f"${current_price_gw:.2f}")
                    gw_cols[1].metric("🏦 Dividendo Anual", f"${last_dividend:.2f}")
                    gw_cols[2].metric("📊 CAGR Dividendo", f"{cagr_gw:.2f}%" if cagr_gw is not None else "N/A")
                    gw_cols[3].metric("📈 Yield Máximo", f"{overall_yield_max:.2%}")
                    gw_cols[4].metric("📉 Yield Mínimo", f"{overall_yield_min:.2%}")
                    gw_cols[5].metric("🚫 Sobrevalorado", f"${last_dividend/overall_yield_min:.2f}")
                    gw_cols[6].metric("✅ Infravalorado", f"${last_dividend/overall_yield_max:.2f}")
                    annual_years = sorted(monthly_data['Año'].unique())
                    annual_bands = []
                    for year in annual_years:
                        div_anual = ajustar_dividendo(year)
                        if div_anual is not None:
                            sobre = div_anual / overall_yield_min
                            infraval = div_anual / overall_yield_max
                            annual_bands.append({
                                "Año": year,
                                "Dividendo Anual": div_anual,
                                "Precio Sobrevalorado": sobre,
                                "Precio Infravalorado": infraval
                            })
                    df_annual = pd.DataFrame(annual_bands)
                    x_sobre = []
                    y_sobre = []
                    x_infra = []
                    y_infra = []
                    for i, row in df_annual.iterrows():
                        year = int(row["Año"])
                        start = pd.to_datetime(f"{year}-01-01")
                        if year != df_annual["Año"].max():
                            end = pd.to_datetime(f"{year+1}-01-01")
                        else:
                            end = price_data_diario.index[-1]
                        x_sobre.extend([start, end])
                        y_sobre.extend([row["Precio Sobrevalorado"], row["Precio Sobrevalorado"]])
                        x_infra.extend([start, end])
                        y_infra.extend([row["Precio Infravalorado"], row["Precio Infravalorado"]])
                    fig_gw = go.Figure()
                    fig_gw.add_trace(go.Scatter(
                        x=price_data_diario.index,
                        y=price_data_diario['Close'],
                        mode='lines',
                        name='Precio Histórico Diario',
                        line=dict(color="hotpink")
                    ))
                    fig_gw.add_trace(go.Scatter(
                        x=x_sobre,
                        y=y_sobre,
                        mode='lines',
                        name='Precio Sobrevalorado',
                        line=dict(color="darkorange", dash="dot")
                    ))
                    fig_gw.add_trace(go.Scatter(
                        x=x_infra,
                        y=y_infra,
                        mode='lines',
                        name='Precio Infravalorado',
                        line=dict(color="deepskyblue", dash="dot")
                    ))
                    fig_gw.add_trace(go.Scatter(
                        x=[price_data_diario.index[-1]],
                        y=[current_price_gw],
                        mode='markers+text',
                        name='Precio Actual',
                        marker=dict(color="hotpink", size=10),
                        text=[f"${current_price_gw:.2f}"],
                        textposition="top center"
                    ))
                    fig_gw.update_layout(
                        title=f"Precio Histórico Diario, Bandas y Precio Actual - {ticker_input}",
                        xaxis_title="Fecha",
                        yaxis_title="Precio ($)",
                        height=500,
                        margin=dict(l=20, r=20, t=60, b=40)
                    )
                    st.plotly_chart(fig_gw, use_container_width=True)
                    st.subheader(f"Datos para el Gráfico de Geraldine Weiss")
                    st.dataframe(df_tabla)
            except Exception as e:
                st.error(f"No se pudo generar el gráfico del Método Geraldine Weiss: {e}")
            # ……………………… (toda tu lógica actual sin cambios) ………………………


        # ==========================
        # BLOQUE 3: Valoración por Múltiplos
        # ==========================
        with st.expander(f"💱 Análisis y Valoración por Múltiplos de {ticker_input}"):

            # ---------- 3-A  Evolución de la Deuda ----------
            st.subheader("💵 Evolución de la Deuda")
            try:
                # Balance y Cash-Flow convertidos a float
                bs = (ticker_data.balance_sheet.transpose()
                                    .apply(pd.to_numeric, errors="coerce"))
                bs.index = bs.index.year

                cf = (ticker_data.cashflow.transpose()
                                    .apply(pd.to_numeric, errors="coerce"))
                cf.index = cf.index.year

                total_debt = bs.get("Total Debt")          or bs.get("Long Term Debt")
                cash       = bs.get("Cash And Cash Equivalents") or bs.get("Cash")
                fcf        = cf.get("Free Cash Flow")

                df_deuda = pd.DataFrame({
                    "FCF":          fcf,
                    "Deuda Neta":   (total_debt - cash) if total_debt is not None and cash is not None else None
                }).dropna(how="all")

                if not df_deuda.empty and "FCF" in df_deuda and "Deuda Neta" in df_deuda:
                    df_deuda["Deuda Neta/FCF"] = df_deuda["Deuda Neta"] / df_deuda["FCF"]
                    df_deuda = df_deuda.replace([np.inf, -np.inf], np.nan).dropna()

                fig_deuda = go.Figure()
                if "FCF" in df_deuda.columns:
                    fig_deuda.add_trace(go.Bar(
                        x=df_deuda.index, y=df_deuda["FCF"],
                        name="FCF", marker_color=primary_orange,
                        text=df_deuda["FCF"].round(0), textposition="outside"
                    ))
                if "Deuda Neta" in df_deuda.columns:
                    fig_deuda.add_trace(go.Bar(
                        x=df_deuda.index, y=df_deuda["Deuda Neta"],
                        name="Deuda Neta", marker_color=primary_blue,
                        text=df_deuda["Deuda Neta"].round(0), textposition="outside"
                    ))
                if "Deuda Neta/FCF" in df_deuda.columns:
                    fig_deuda.add_trace(go.Scatter(
                        x=df_deuda.index, y=df_deuda["Deuda Neta/FCF"],
                        name="Deuda Neta/FCF", mode="lines+markers+text",
                        yaxis="y2", line=dict(color=primary_pink),
                        text=[f"{v:.2f}" for v in df_deuda["Deuda Neta/FCF"]],
                        textposition="top right"
                    ))

                fig_deuda.update_layout(
                    title="Evolución de Deuda, FCF y Deuda Neta/FCF",
                    xaxis_title="Año", yaxis_title="Millones USD",
                    yaxis2=dict(title="Deuda Neta/FCF", overlaying="y", side="right"),
                    barmode="group", height=500,
                    margin=dict(l=30, r=30, t=60, b=30)
                )
                st.plotly_chart(fig_deuda, use_container_width=True, key="plotly_chart_deuda")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de deuda: {e}")

            # ---------- 3-B  Histórico PER ----------
            st.subheader("📈 Histórico del PER, EPS y Precio")
            try:
                st.subheader(f"📌 El PER actual es de {pe_ratio:.2f}x")
                income_statement = ticker_data.financials

                if "Basic EPS" not in income_statement.index:
                    st.warning("No se encontró 'Basic EPS'.")
                else:
                    eps_series = pd.to_numeric(income_statement.loc["Basic EPS"], errors="coerce")
                    eps_series.index = pd.to_datetime(eps_series.index).year
                    price_yearly = pd.to_numeric(
                        price_data.resample("Y").last()["Close"], errors="coerce")
                    price_yearly.index = price_yearly.index.year

                    df_per = (pd.DataFrame({
                                "EPS": eps_series, "Precio": price_yearly
                            })
                            .dropna())
                    df_per["PER"] = df_per["Precio"] / df_per["EPS"]
                    df_per = df_per.replace([np.inf, -np.inf], np.nan).dropna()

                    fig_combined = go.Figure()
                    fig_combined.add_trace(go.Bar(
                        x=df_per.index, y=df_per["EPS"],
                        name="EPS", marker_color=primary_orange,
                        text=df_per["EPS"].round(2), textposition="outside"))
                    fig_combined.add_trace(go.Bar(
                        x=df_per.index, y=df_per["Precio"],
                        name="Precio", marker_color=primary_blue,
                        text=df_per["Precio"].round(2), textposition="outside"))
                    fig_combined.add_trace(go.Scatter(
                        x=df_per.index, y=df_per["PER"],
                        name="PER", mode="lines+markers+text",
                        yaxis="y2", line=dict(color=primary_pink),
                        text=[f"{v:.2f}" for v in df_per["PER"]],
                        textposition="top right"))
                    fig_combined.update_layout(
                        title="Histórico del EPS, Precio y PER",
                        xaxis_title="Año",
                        yaxis=dict(title="EPS / Precio"),
                        yaxis2=dict(title="PER", overlaying="y", side="right"),
                        barmode="group", height=450,
                        margin=dict(l=30, r=30, t=60, b=30))
                    st.plotly_chart(fig_combined, use_container_width=True, key="plotly_chart_per")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico PER: {e}")

            # ---------- 3-C  EV / EBITDA ----------
            st.subheader("📐 Evolución de EV, EBITDA y EV/EBITDA")
            try:
                income = (ticker_data.financials.transpose()
                                        .apply(pd.to_numeric, errors="coerce"))
                income.index = income.index.year
                ebitda = income.get("EBITDA")

                bs = (ticker_data.balance_sheet.transpose()
                                    .apply(pd.to_numeric, errors="coerce"))
                bs.index = bs.index.year
                total_debt = bs.get("Total Debt") or bs.get("Long Term Debt")
                cash       = bs.get("Cash And Cash Equivalents") or bs.get("Cash")
                net_debt   = total_debt - cash if total_debt is not None and cash is not None else None

                market_cap = ticker_data.info.get("marketCap")

                if ebitda is not None and net_debt is not None and market_cap is not None:
                    ev = market_cap + net_debt
                    ev_ebitda = ev / ebitda
                else:
                    ev = ev_ebitda = None

                df_ev = pd.DataFrame({
                    "EBITDA": ebitda,
                    "EV": ev,
                    "EV/EBITDA": ev_ebitda
                }).dropna(how="all")

                # EV/EBITDA actual (último año)
                current_ev_ebitda = df_ev["EV/EBITDA"].dropna().iloc[-1] if "EV/EBITDA" in df_ev and not df_ev["EV/EBITDA"].dropna().empty else None
                st.subheader(f"📌 EV/EBITDA actual: {current_ev_ebitda:.2f}" if current_ev_ebitda is not None else "EV/EBITDA actual no disponible")

                fig_ev = go.Figure()
                if "EBITDA" in df_ev:
                    fig_ev.add_trace(go.Bar(
                        x=df_ev.index, y=df_ev["EBITDA"],
                        name="EBITDA", marker_color=primary_orange,
                        text=df_ev["EBITDA"].round(0), textposition="outside"))
                if "EV" in df_ev:
                    fig_ev.add_trace(go.Bar(
                        x=df_ev.index, y=df_ev["EV"],
                        name="EV", marker_color=primary_blue,
                        text=df_ev["EV"].round(0), textposition="outside"))
                if "EV/EBITDA" in df_ev:
                    fig_ev.add_trace(go.Scatter(
                        x=df_ev.index, y=df_ev["EV/EBITDA"],
                        name="EV/EBITDA", mode="lines+markers+text",
                        yaxis="y2", line=dict(color=primary_pink),
                        text=[f"{v:.2f}" for v in df_ev["EV/EBITDA"]],
                        textposition="top right"))
                fig_ev.update_layout(
                    title="Evolución de EV, EBITDA y EV/EBITDA",
                    xaxis_title="Año", yaxis_title="Valor (USD)",
                    yaxis2=dict(title="EV/EBITDA", overlaying="y", side="right"),
                    barmode="group", height=500,
                    margin=dict(l=30, r=30, t=60, b=30))
                st.plotly_chart(fig_ev, use_container_width=True, key="plotly_chart_ev")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico EV/EBITDA: {e}")

        # ==========================
        # BLOQUE 4: Análisis Fundamental - Balance
        # ==========================
        with st.expander(f"⚖️ Análisis Fundamental - Balance de {ticker_input}"):

            # ------------------------------------------------------------------
            # 4-A  Activos totales vs corrientes
            # ------------------------------------------------------------------
            st.subheader("🏢 Evolución de Activos Totales y Activos Corrientes")
            try:
                bs_t = (ticker_data.balance_sheet.transpose()
                                        .apply(pd.to_numeric, errors="coerce")
                                        .dropna(how="all"))
                bs_t.index = bs_t.index.year

                if "Total Assets" not in bs_t.columns:
                    st.warning("No se encontró 'Total Assets' en el Balance Sheet.")
                else:
                    total_assets = bs_t["Total Assets"]
                    found_current_assets = next(
                        (c for c in ["Current Assets", "Total Current Assets"] if c in bs_t.columns),
                        None)

                    if found_current_assets is None:
                        st.warning("No se encontró información sobre Activos Corrientes.")
                    else:
                        current_assets = bs_t[found_current_assets]

                        df_activos = (pd.DataFrame({
                            "Total Assets": total_assets,
                            found_current_assets: current_assets
                        })
                        .replace([np.inf, -np.inf], np.nan)
                        .dropna(how="all"))

                        fig_activos = go.Figure()
                        if not df_activos["Total Assets"].dropna().empty:
                            fig_activos.add_trace(go.Bar(
                                x=df_activos.index,
                                y=df_activos["Total Assets"],
                                name="Total Assets",
                                marker_color=primary_blue,
                                text=df_activos["Total Assets"].round(0),
                                textposition="outside"))
                        if not df_activos[found_current_assets].dropna().empty:
                            fig_activos.add_trace(go.Bar(
                                x=df_activos.index,
                                y=df_activos[found_current_assets],
                                name=found_current_assets,
                                marker_color=primary_orange,
                                text=df_activos[found_current_assets].round(0),
                                textposition="outside"))

                        fig_activos.update_layout(
                            title="Evolución de Activos Totales y Activos Corrientes",
                            xaxis_title="Año", yaxis_title="Valor (USD)",
                            barmode="group", height=450,
                            margin=dict(l=30, r=30, t=60, b=30))
                        st.plotly_chart(fig_activos, use_container_width=True, key="plotly_chart_activos")
                        st.markdown("#### Datos de Activos")
                        st.dataframe(df_activos)
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de activos: {e}")

            # ------------------------------------------------------------------
            # 4-B  Pasivos totales / corrientes + Deuda
            # ------------------------------------------------------------------
            st.subheader("💳 Evolución de Pasivos Totales y Pasivos Corrientes Totales")
            try:
                bs_t = (ticker_data.balance_sheet.transpose()
                                        .apply(pd.to_numeric, errors="coerce")
                                        .dropna(how="all"))
                bs_t.index = bs_t.index.year

                if "Total Liabilities Net Minority Interest" not in bs_t.columns:
                    st.warning("No se encontró 'Total Liabilities Net Minority Interest'.")
                else:
                    total_liabilities = bs_t["Total Liabilities Net Minority Interest"]
                    found_current = next((c for c in
                                        ["Current Liabilities", "Total Current Liabilities"]
                                        if c in bs_t.columns), None)

                    if found_current is None:
                        st.warning("No se encontró información sobre Pasivos Corrientes.")
                    else:
                        current_liabilities = bs_t[found_current]

                        df_pasivos = (pd.DataFrame({
                            "Total Liabilities": total_liabilities,
                            found_current: current_liabilities
                        })
                        .replace([np.inf, -np.inf], np.nan)
                        .dropna(how="all"))

                        fig_pasivos = go.Figure()
                        fig_pasivos.add_trace(go.Bar(
                            x=df_pasivos.index, y=df_pasivos["Total Liabilities"],
                            name="Total Liabilities", marker_color=primary_blue,
                            text=df_pasivos["Total Liabilities"].round(0),
                            textposition="outside"))
                        fig_pasivos.add_trace(go.Bar(
                            x=df_pasivos.index, y=df_pasivos[found_current],
                            name=found_current, marker_color=primary_orange,
                            text=df_pasivos[found_current].round(0),
                            textposition="outside"))

                        fig_pasivos.update_layout(
                            title="Evolución de Pasivos Totales y Pasivos Corrientes Totales",
                            xaxis_title="Año", yaxis_title="Valor (USD)",
                            barmode="group", height=450,
                            margin=dict(l=30, r=30, t=60, b=30))
                        st.plotly_chart(fig_pasivos, use_container_width=True, key="plotly_pasivos")
                        st.markdown("#### Datos de Pasivos")
                        st.dataframe(df_pasivos)

                # ---------- Deuda total vs neta ----------
                st.subheader("💰 Evolución de Deuda Total vs Deuda Neta")
                total_debt = bs_t.get("Total Debt")
                net_debt   = bs_t.get("Net Debt")
                if total_debt is None or net_debt is None:
                    st.warning("No se encontraron ambos campos 'Total Debt' y 'Net Debt'.")
                else:
                    df_debt = (pd.DataFrame({"Total Debt": total_debt, "Net Debt": net_debt})
                                .replace([np.inf, -np.inf], np.nan)
                                .dropna(how="all"))

                    fig_debt = go.Figure()
                    fig_debt.add_trace(go.Bar(
                        x=df_debt.index, y=df_debt["Total Debt"],
                        name="Total Debt", marker_color=primary_blue,
                        text=df_debt["Total Debt"].round(0), textposition="outside"))
                    fig_debt.add_trace(go.Bar(
                        x=df_debt.index, y=df_debt["Net Debt"],
                        name="Net Debt", marker_color=primary_pink,
                        text=df_debt["Net Debt"].round(0), textposition="outside"))
                    fig_debt.update_layout(
                        title="Evolución de Deuda Total y Deuda Neta",
                        xaxis_title="Año", yaxis_title="Valor (USD)",
                        barmode="group", height=450,
                        margin=dict(l=30, r=30, t=60, b=30))
                    st.plotly_chart(fig_debt, use_container_width=True, key="plotly_debt")
                    st.markdown("#### Datos de Deuda")
                    st.dataframe(df_debt)
            except Exception as e:
                st.warning(f"No se pudo generar los gráficos de pasivos/deuda: {e}")

            # ------------------------------------------------------------------
            # 4-C  Patrimonio
            # ------------------------------------------------------------------
            st.subheader("💼 Evolución del Patrimonio")
            try:
                bs_t = (ticker_data.balance_sheet.transpose()
                                        .apply(pd.to_numeric, errors="coerce"))
                bs_t.index = bs_t.index.year

                total_equity = bs_t.get("Total Equity Gross Minority Interest")
                if total_equity is None:
                    st.warning("No se encontró 'Total Equity Gross Minority Interest'.")
                else:
                    df_capital = total_equity.to_frame("Total Equity")
                    fig_capital = go.Figure()
                    fig_capital.add_trace(go.Bar(
                        x=df_capital.index, y=df_capital["Total Equity"],
                        name="Total Equity", marker_color=primary_orange,
                        text=df_capital["Total Equity"].round(0), textposition="outside"))
                    fig_capital.update_layout(
                        title="Evolución del Patrimonio",
                        xaxis_title="Año", yaxis_title="Valor (USD)",
                        height=450, margin=dict(l=30, r=30, t=60, b=30))
                    st.plotly_chart(fig_capital, use_container_width=True,
                                    key="plotly_chart_capital")
                    st.markdown("#### Datos del Patrimonio")
                    st.dataframe(df_capital)
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de Patrimonio: {e}")

            # ------------------------------------------------------------------
            # 4-D  Visión 3-líneas (Assets / Liabilities / Equity)
            # ------------------------------------------------------------------
            st.subheader("⏳ Evolución del Balance")
            try:
                bs_t = (ticker_data.balance_sheet.transpose()
                                        .apply(pd.to_numeric, errors="coerce"))
                bs_t.index = bs_t.index.year

                req = ["Total Assets", "Total Liabilities Net Minority Interest",
                    "Total Equity Gross Minority Interest"]
                if any(c not in bs_t.columns for c in req):
                    st.warning("Faltan columnas clave para la vista de balance.")
                else:
                    df_balance = bs_t[req].replace([np.inf, -np.inf], np.nan).dropna(how="all")
                    fig_balance = go.Figure()
                    fig_balance.add_trace(go.Scatter(
                        x=df_balance.index, y=df_balance["Total Assets"],
                        mode="lines+markers", name="Total Assets",
                        line=dict(color=primary_blue)))
                    fig_balance.add_trace(go.Scatter(
                        x=df_balance.index, y=df_balance["Total Liabilities Net Minority Interest"],
                        mode="lines+markers", name="Total Liabilities",
                        line=dict(color=primary_orange)))
                    fig_balance.add_trace(go.Scatter(
                        x=df_balance.index, y=df_balance["Total Equity Gross Minority Interest"],
                        mode="lines+markers", name="Total Equity",
                        line=dict(color=primary_pink)))
                    fig_balance.update_layout(
                        title="Evolución del Balance: Activos, Pasivos y Capital",
                        xaxis_title="Año", yaxis_title="Valor (USD)",
                        height=450, margin=dict(l=30, r=30, t=60, b=30))
                    st.plotly_chart(fig_balance, use_container_width=True,
                                    key="plotly_chart_balance")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico del Balance: {e}")

            # ------------------------------------------------------------------
            # Tabla completa
            # ------------------------------------------------------------------
            st.markdown("#### Balance en detalle")
            st.dataframe(ticker_data.balance_sheet.iloc[::-1], height=300)



            # BLOQUE 5: Análisis Fundamental - Estado de Resultados
        # ==========================
        with st.expander(f"📝 Análisis Fundamental - Estado de Resultados de {ticker_input}"):

            # ------------------------------------------------------------------
            # 5-A  Ingresos
            # ------------------------------------------------------------------
            st.subheader("📝 Evolución de los Ingresos")
            try:
                income = (ticker_data.financials.transpose()
                                        .apply(pd.to_numeric, errors="coerce")
                                        .replace([np.inf, -np.inf], np.nan)
                                        .dropna(how="all"))
                income.index = income.index.year

                if not {"Total Revenue", "Gross Profit", "Operating Income"} <= set(income.columns):
                    st.warning("No hay suficientes datos para graficar ingresos.")
                else:
                    df_income = income[["Total Revenue", "Gross Profit", "Operating Income"]].copy()
                    if "Net Income" in income.columns:
                        df_income["Net Income"] = income["Net Income"]
                    elif "Net Income from Continuing Operation Net Minority Interest" in income.columns:
                        df_income["Net Income"] = income["Net Income from Continuing Operation Net Minority Interest"]

                    df_income = df_income.dropna(how="all")          # evita barras huecas

                    primary_gold = "gold"
                    fig_income = go.Figure()
                    for col, color in zip(df_income.columns,
                                        [primary_blue, primary_orange,
                                        primary_pink, primary_gold][:len(df_income.columns)]):
                        serie = df_income[col].dropna()
                        if not serie.empty:
                            fig_income.add_trace(go.Bar(
                                x=serie.index, y=serie.values, name=col,
                                marker_color=color,
                                text=[f"${v:,.0f}" for v in serie],
                                textposition="outside"))

                    fig_income.update_layout(
                        title="Evolución de los Ingresos",
                        xaxis_title="Año", yaxis_title="Valor (USD)",
                        barmode="group", height=450,
                        margin=dict(l=30, r=30, t=60, b=30))
                    st.plotly_chart(fig_income, use_container_width=True)
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de Ingresos: {e}")

            # ------------------------------------------------------------------
            # 5-B  Márgenes
            # ------------------------------------------------------------------
            st.subheader("📝 Evolución de Márgenes")
            try:
                ingresos = income.get("Total Revenue")
                if ingresos is None:
                    st.warning("No hay columna 'Total Revenue'; no se calculan márgenes.")
                else:
                    series_margenes = {}
                    if "Gross Profit" in income.columns:
                        series_margenes["Margen Bruto (%)"] = (income["Gross Profit"] / ingresos * 100)
                    if "Operating Income" in income.columns:
                        series_margenes["Margen Operativo (%)"] = (income["Operating Income"] / ingresos * 100)
                    if "Net Income" in income.columns:
                        series_margenes["Margen Neto (%)"] = (income["Net Income"] / ingresos * 100)

                    fig = go.Figure()
                    for nombre, serie in series_margenes.items():
                        serie = (serie.replace([np.inf, -np.inf], np.nan)
                                    .dropna()
                                    .round(1))
                        if not serie.empty:
                            color = {"Margen Bruto (%)": primary_blue,
                                    "Margen Operativo (%)": primary_orange,
                                    "Margen Neto (%)": primary_pink}[nombre]
                            fig.add_trace(go.Scatter(x=serie.index, y=serie.values,
                                                    mode="lines+markers", name=nombre,
                                                    line=dict(color=color)))
                    if not fig.data:
                        st.warning("Sin datos suficientes para márgenes.")
                    else:
                        fig.update_layout(
                            title="Evolución de Márgenes (% sobre ventas)",
                            xaxis_title="Año", yaxis_title="% Margen",
                            height=450,
                            margin=dict(l=30, r=30, t=60, b=30))
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de márgenes: {e}")

            # ------------------------------------------------------------------
            # 5-C  EPS
            # ------------------------------------------------------------------
            st.subheader("⏳ Evolución del EPS")
            try:
                if eps_actual is not None:
                    st.subheader(f"📌 El EPS actual es de ${eps_actual:.2f}")
                else:
                    st.warning("EPS actual no disponible.")

                diluted_eps = income.get("Diluted EPS")
                if diluted_eps is None:
                    st.warning("No se encontró 'Diluted EPS' para este ticker.")
                else:
                    diluted_eps = diluted_eps.dropna()
                    fig_eps = go.Figure()
                    fig_eps.add_trace(go.Bar(
                        x=diluted_eps.index, y=diluted_eps.values,
                        name="Diluted EPS", marker_color=primary_orange,
                        text=[f"${v:.2f}" for v in diluted_eps],
                        textposition="outside"))
                    fig_eps.update_layout(
                        title="Evolución del Diluted EPS",
                        xaxis_title="Año", yaxis_title="Diluted EPS (USD)",
                        height=450, margin=dict(l=30, r=30, t=60, b=30))
                    st.plotly_chart(fig_eps, use_container_width=True,
                                    key="plotly_chart_eps")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de Diluted EPS: {e}")

            # ------------------------------------------------------------------
            # 5-D  Acciones en circulación
            # ------------------------------------------------------------------
            st.subheader("🔄 Evolución de Acciones en Circulación")
            try:
                bs = ticker_data.balance_sheet
                if "Ordinary Shares Number" not in bs.index:
                    st.warning("No se encontró 'Ordinary Shares Number' en el Balance Sheet.")
                else:
                    ordinary = (bs.loc["Ordinary Shares Number"]
                                .apply(pd.to_numeric, errors="coerce")
                                .dropna())
                    ordinary.index = pd.to_datetime(ordinary.index).year
                    ordinary = ordinary.sort_index()
                    ordinary_y = ordinary.resample("Y").last().dropna()
                    ordinary_y.index = ordinary_y.index.year

                    if ordinary_y.empty:
                        st.warning("No hay datos válidos de acciones en circulación.")
                    else:
                        fig_shares = go.Figure()
                        fig_shares.add_trace(go.Bar(
                            x=ordinary_y.index, y=ordinary_y.values,
                            name="Acciones en Circulación", marker_color=primary_blue,
                            text=[f"{int(v):,}" for v in ordinary_y],
                            textposition="outside"))
                        fig_shares.update_layout(
                            title="Evolución de Acciones en Circulación",
                            xaxis_title="Año", yaxis_title="Acciones",
                            height=450, margin=dict(l=30, r=30, t=60, b=30))
                        st.plotly_chart(fig_shares, use_container_width=True)
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico de Acciones en Circulación: {e}")

            # ------------------------------------------------------------------
            # Tabla completa
            # ------------------------------------------------------------------
            st.markdown("#### Estado de Resultados en detalle")
            st.dataframe(ticker_data.financials.iloc[::-1], height=300)

        # ==========================
        # BLOQUE 6: Estado de Flujo de Efectivo
        # ==========================
        with st.expander(f"💵 Análisis Fundamental - Estado de Flujo de Efectivo de {ticker_input}"):

            # ------------------------------------------------------------------
            # 6-A  Pre-procesamiento del Cash-Flow
            # ------------------------------------------------------------------
            cf = (ticker_data.cashflow.transpose()
                    .apply(pd.to_numeric, errors="coerce")
                    .replace([np.inf, -np.inf], np.nan)
                    .dropna(how="all"))
            cf.index = pd.to_datetime(cf.index, errors="coerce").year

            # copia para series “anchas”
            cf_t = cf.copy()

            # ------------------------------------------------------------------
            # 6-B  Operating CF, CapEx y FCF (%)
            # ------------------------------------------------------------------
            st.subheader("🛒 Flujo de Caja: Operating CF, CaPex y FCF (%)")
            try:
                if {"Operating Cash Flow", "Capital Expenditure"} <= set(cf.columns):
                    op_cf  = cf["Operating Cash Flow"].dropna()
                    capex  = cf["Capital Expenditure"].dropna()
                    adj_capex = -capex                               # signo positivo ↓
                    fcf   = (op_cf + capex).dropna()
                    fcf_pct = (fcf / op_cf.replace(0, np.nan) * 100).replace([np.inf, -np.inf], np.nan)

                    fig_cf = go.Figure()
                    for serie, name, color in [
                        (op_cf,      "Operating Cash Flow",           primary_blue),
                        (adj_capex,  "Capital Expenditure (abs)",     primary_orange)]:
                        if not serie.empty:
                            fig_cf.add_trace(go.Bar(
                                x=serie.index, y=serie.values, name=name,
                                marker_color=color,
                                text=[f"${v:,.0f}" for v in serie],
                                textposition="outside"))
                    # línea FCF %
                    if not fcf_pct.dropna().empty:
                        fig_cf.add_trace(go.Scatter(
                            x=fcf_pct.index, y=fcf_pct.values,
                            name="FCF (%)", mode="lines+markers+text",
                            yaxis="y2", line=dict(color=primary_pink),
                            text=[f"{v:.1f}%" for v in fcf_pct],
                            textposition="top right"))

                    fig_cf.update_layout(
                        title="Flujo de Caja: Operating CF, CaPex y FCF (%)",
                        xaxis_title="Año",
                        yaxis=dict(title="Valores (USD)"),
                        yaxis2=dict(title="FCF (%)", overlaying="y", side="right"),
                        barmode="group", height=450,
                        margin=dict(l=30, r=30, t=60, b=30))
                    st.plotly_chart(fig_cf, use_container_width=True, key="plotly_chart_cf")
                else:
                    st.warning("No se encontraron 'Operating Cash Flow' o 'Capital Expenditure'.")
            except Exception as e:
                st.warning(f"No se pudo generar el gráfico combinado: {e}")

            # ------------------------------------------------------------------
            # 6-C  Emisión / Pago de deuda y Recompra de acciones
            # ------------------------------------------------------------------
            def barra_simple(serie: pd.Series, titulo: str, color: str, key_plot: str):
                serie = pd.to_numeric(serie, errors="coerce").dropna()
                if serie.empty:
                    st.warning(f"No hay datos para {titulo.lower()}.")
                    return
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=serie.index, y=serie.values,
                    name=titulo, marker_color=color,
                    text=[f"${v:,.0f}" for v in serie],
                    textposition="outside"))
                fig.update_layout(
                    title=titulo, xaxis_title="Año", yaxis_title="Valor (USD)",
                    height=450, margin=dict(l=30, r=30, t=60, b=30))
                st.plotly_chart(fig, use_container_width=True, key=key_plot)
                return serie

            # Emisión
            st.subheader("💳 Emisión de Deuda")
            issuance = barra_simple(cf_t.get("Issuance Of Debt"), "Emisión de Deuda",
                                    primary_blue, "plotly_chart_issuance")

            # tendencia sólo si hay ≥2 puntos
            if issuance is not None and len(issuance) > 1:
                fig = st.session_state.get("plotly_chart_issuance")
                serie_clean = issuance.dropna()
                if len(serie_clean) > 1:
                    coef = np.polyfit(serie_clean.index.astype(float), serie_clean.values, 1)
                    trend = coef[0] * serie_clean.index + coef[1]
                    fig.add_trace(go.Scatter(
                        x=serie_clean.index, y=trend,
                        mode="lines", name="Tendencia",
                        line=dict(color="hotpink", dash="dash")))

            # Pago
            st.subheader("🏛️ Pago de Deuda")
            barra_simple(cf_t.get("Repayment Of Debt"), "Pago de Deuda",
                        primary_orange, "plotly_chart_repayment")

            # Recompra
            st.subheader("♻️ Recompra de Acciones")
            barra_simple(cf_t.get("Repurchase Of Capital Stock"), "Recompra de Acciones",
                        primary_pink, "plotly_chart_repurchase")

            # ------------------------------------------------------------------
            # 6-D  Tabla
            # ------------------------------------------------------------------
            st.markdown("#### Estado de Flujo de Efectivo en detalle")
            st.dataframe(ticker_data.cashflow.iloc[::-1], height=300)


    # --------------------------
        # Sección: Precios Objetivo (con entrada de Yield Deseado aquí)
        # --------------------------
        
        st.markdown("## 🎯 Valoración Proyectada")
        key_cols = st.columns(4)
        key_cols[0].metric("💰 Precio Actual", f"${price:.2f}" if price is not None else "N/A")
        # Para calcular el Valor Infravalorado de Geraldine Weiss se utiliza la metodología a partir de datos diarios:
        price_data_diario = ticker_data.history(period=selected_period, interval="1d")
        dividends_daily = ticker_data.dividends
        if not dividends_daily.empty:
                annual_dividends_raw = dividends_daily.resample("Y").sum()
                annual_dividends_raw.index = annual_dividends_raw.index.year
                start_year = pd.to_datetime(price_data.index[0]).year
                end_year = pd.to_datetime(price_data.index[-1]).year
                annual_dividends_gw = annual_dividends_raw[(annual_dividends_raw.index >= start_year) & (annual_dividends_raw.index <= end_year)]
                if len(annual_dividends_gw) >= 3:
                    first_val_gw = annual_dividends_gw.iloc[0]
                    penultimate_val_gw = annual_dividends_gw.iloc[-2]
                    n_years_gw = annual_dividends_gw.index[-2] - annual_dividends_gw.index[0]
                    cagr_gw = ((penultimate_val_gw / first_val_gw) ** (1 / n_years_gw) - 1) * 100
                else:
                    cagr_gw = None
                current_year = pd.Timestamp.today().year
                def ajustar_dividendo(year):
                    if (year == current_year) and (cagr_gw is not None) and ((year - 1) in annual_dividends_gw.index):
                        return annual_dividends_gw[year - 1] * (1 + cagr_gw/100)
                    else:
                        return annual_dividends_gw.get(year, None)
                    monthly_data = price_data_diario.resample("M").last().reset_index()
                    monthly_data['Año'] = monthly_data['Date'].dt.year
                    monthly_data['Mes'] = monthly_data['Date'].dt.strftime("%B")
                    monthly_data.rename(columns={'Close': 'Precio'}, inplace=True)
                    monthly_data['Dividendo Anual'] = monthly_data['Año'].apply(ajustar_dividendo)
                    monthly_data['Yield'] = monthly_data['Dividendo Anual'] / monthly_data['Precio']
                    overall_yield_max = monthly_data['Yield'].max()
                    monthly_data['Precio Infravalorado'] = monthly_data['Dividendo Anual'] / overall_yield_max
                    monthly_data = monthly_data.sort_values(by='Date')
                    valor_infravalorado = monthly_data.iloc[-1]['Precio Infravalorado']
        else:
                    valor_infravalorado = None
                        
        key_cols[1].metric("💎 Precio Infrav. G. Weiss", f"${valor_infravalorado:.2f}" if valor_infravalorado is not None else "N/A")
        key_cols[2].metric("📊 Valor Libro Precio Justo", f"${fair_price:.2f}" if fair_price is not None else "N/A")
        key_cols[3].metric("🚀 Precio a PER 5 años", f"${per_5y:.2f}" if per_5y is not None else "N/A")
                        
                # Ahora, en esta misma sección se solicita el Yield Deseado
        yield_deseado_obj = st.number_input("Ingrese Aquí el Yield Deseado (%)", min_value=0.1, value=3.0, step=0.1, key="yield_deseado_objetivo")
                        
                # Recalcular el Precio por Dividendo Esperado:
                # (Dividendo Actual * (1 + (CAGR del Dividendo)/100)) / (Yield Deseado/100)
        fair_div_price = (dividend * (1 + (cagr_dividend/100))) / (yield_deseado_obj/100) if (dividend is not None and cagr_dividend is not None and yield_deseado_obj != 0) else None
                        
        st.metric("⌛ Precio por Dividendo Esperado", f"${fair_div_price:.2f}" if fair_div_price is not None else "N/A")
                        
                # --------------------------
                # Datos Relevantes (tabla)
                # --------------------------
        otros_datos = {
                            "ROE Actual": f"{roe_actual*100:.2f}%" if roe_actual is not None else "N/A",
                            "PauOut": f"{payout_ratio*100:.2f}%" if payout_ratio is not None else "N/A",
                            "EPS Actual": f"${eps_actual:.2f}" if eps_actual is not None else "N/A",
                            "PER": f"{pe_ratio:.2f}" if pe_ratio is not None else "N/A",
                            "P/B": f"{pb:.2f}" if pb is not None else "N/A",
                            "Book/Share": f"${book_per_share:.2f}" if book_per_share is not None else "N/A",
                            "G": f"{G_percent:.2f}%" if G_percent is not None else "N/A",
                            "Múltiplo Crecimiento": f"{multiplier}" if multiplier is not None else "N/A",
                            "EPS a 5 años": f"${eps_5y:.2f}" if eps_5y is not None else "N/A",
                            "G esperado": f"{g_esperado_percent:.2f}%" if g_esperado_percent is not None else "N/A",
                            "Dividendo Anual": f"${dividend:.2f}" if dividend is not None else "N/A",
                            "Yield Actual": f"{yield_actual:.2f}%" if yield_actual is not None else "N/A",
                            "CAGR del Dividendo": f"{cagr_dividend:.2f}%" if cagr_dividend is not None else "N/A",
                            "Yield Promedio": f"{avg_yield:.2f}%" if avg_yield is not None else "N/A"
                        }
        df_otros = pd.DataFrame.from_dict(otros_datos, orient='index', columns=["Valor"])
        st.markdown("### 👨‍💻 Datos Relevantes")
        st.dataframe(df_otros)
        st.subheader("")


    except Exception as e: 
        st.error(f"Ocurrió un error al obtener los datos: {e}")
