Python 
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ---------------------------------------------------------
# CONFIGURAZIONE PAGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="VWCE Pro Financial Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS Custom per look Terminal Professionale
st.markdown("""
<style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; padding: 12px; border-radius: 8px; border: 1px solid #30363d; }
    div[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DEFINIZIONE TICKER E HOOKS
# ---------------------------------------------------------
VWCE_TICKER = "VWCE.DE" # Xetra Milano/Germania

TOP_HOLDINGS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Meta": "META",
    "Alphabet": "GOOGL",
    "Broadcom": "AVGO",
    "Tesla": "TSLA",
    "Eli Lilly": "LLY",
    "JPMorgan": "JPM"
}

DEFENSE_HOLDINGS = {
    "Lockheed Martin": "LMT",
    "RTX Corp": "RTX",
    "Northrop Grumman": "NOC",
    "General Dynamics": "GD",
    "Rheinmetall": "RHM.DE",
    "BAE Systems": "BA.L",
    "Leonardo": "LDO.MI"
}

MACRO_INDICATORS = {
    "S&P 500": "^GSPC",
    "Nasdaq 100": "^IXIC",
    "Petolio Brent": "BZ=F",
    "Oro (Gold)": "GC=F",
    "VIX (Volatilità)": "^VIX",
    "BTP 10Y Italia": "BTP=F"
}

# ---------------------------------------------------------
# FUNZIONI DI CARICAMENTO DATI AUTOMATIZZATO (TTL = 15 MINUTI)
# ---------------------------------------------------------
@st.cache_data(ttl=900)
def fetch_etf_history(ticker, period="1y"):
    etf = yf.Ticker(ticker)
    df = etf.history(period=period)
    return df, etf.info, etf.news

@st.cache_data(ttl=900)
def fetch_group_performance(tickers_dict):
    records = []
    for name, sym in tickers_dict.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if len(h) >= 2:
                last = h['Close'].iloc[-1]
                prev = h['Close'].iloc[-2]
                chg = ((last - prev) / prev) * 100
                records.append({
                    "Nome": name,
                    "Ticker": sym,
                    "Prezzo": round(last, 2),
                    "Variazione 1G (%)": round(chg, 2),
                    "Volume": int(h['Volume'].iloc[-1])
                })
        except Exception:
            pass
    return pd.DataFrame(records)

# ---------------------------------------------------------
# SIDEBAR CONTROL
# ---------------------------------------------------------
st.sidebar.title("⚡ VWCE Terminal v2.0")
st.sidebar.caption(f"Ultimo aggiornamento automatico: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

timeframe = st.sidebar.select_slider(
    "Orizzonte Temporale Grafici",
    options=["1mo", "3mo", "6mo", "1y", "2y", "5y", "max"],
    value="1y"
)

st.sidebar.markdown("---")
st.sidebar.subheader("📐 Simulatore PAC")
pac_monthly = st.sidebar.number_input("Quota Mensile (€)", value=500, step=50)
pac_years = st.sidebar.slider("Orizzonte (Anni)", 1, 30, 15)
expected_return = st.sidebar.slider("Rendimento Annuo Stimato (%)", 3.0, 12.0, 7.0)

# ---------------------------------------------------------
# CARICAMENTO DATI
# ---------------------------------------------------------
with st.spinner("Connessione ai mercati in corso..."):
    df_vwce, info_vwce, news_vwce = fetch_etf_history(VWCE_TICKER, timeframe)
    df_tech = fetch_group_performance(TOP_HOLDINGS)
    df_defense = fetch_group_performance(DEFENSE_HOLDINGS)
    df_macro = fetch_group_performance(MACRO_INDICATORS)

# ---------------------------------------------------------
# HEADER & METRICHE VWCE IN TEMPO REALE
# ---------------------------------------------------------
st.title("📈 Vanguard FTSE All-World (VWCE) - Real-Time Dashboard")

if not df_vwce.empty:
    curr_price = df_vwce['Close'].iloc[-1]
    prev_price = df_vwce['Close'].iloc[-2] if len(df_vwce) > 1 else curr_price
    diff = curr_price - prev_price
    pct_diff = (diff / prev_price) * 100

    # Calcolo indicatori tecnici di base
    returns = df_vwce['Close'].pct_change().dropna()
    volatility_ann = returns.std() * np.sqrt(252) * 100
    sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() != 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Prezzo VWCE", f"{curr_price:.2f} €", f"{diff:+.2f} € ({pct_diff:+.2f}%)")
    col2.metric("Volatilità Annua", f"{volatility_ann:.2f}%")
    col3.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
    col4.metric("Max Giornaliero", f"{df_vwce['High'].iloc[-1]:.2f} €")
    col5.metric("Min Giornaliero", f"{df_vwce['Low'].iloc[-1]:.2f} €")

st.markdown("---")

# ---------------------------------------------------------
# TAB NAVIGATION
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Grafico e Analisi Tecnica",
    "🏢 Tech & Big Holdings",
    "🛡️ Settore Difesa & Geopolitica",
    "🌍 Macro & Commodity",
    "🧮 Simulatore PAC & Monte Carlo"
])

# TAB 1: GRAFICO INTERATTIVO
with tab1:
    st.subheader("Analisi Storica e Medie Mobili")
    
    # Calcolo Medie Mobili
    df_vwce['SMA50'] = df_vwce['Close'].rolling(window=50).mean()
    df_vwce['SMA200'] = df_vwce['Close'].rolling(window=200).mean()
    
    fig_main = go.Figure()
    fig_main.add_trace(go.Scatter(x=df_vwce.index, y=df_vwce['Close'], name='VWCE Price', line=dict(color='#0066FF', width=2)))
    fig_main.add_trace(go.Scatter(x=df_vwce.index, y=df_vwce['SMA50'], name='SMA 50', line=dict(color='#FF9900', width=1)))
    fig_main.add_trace(go.Scatter(x=df_vwce.index, y=df_vwce['SMA200'], name='SMA 200', line=dict(color='#FF0055', width=1)))
    
    fig_main.update_layout(template="plotly_dark", height=500, margin=dict(l=10, r=10, t=20, b=20))
    st.plotly_chart(fig_main, use_container_width=True)

# TAB 2: TECH HOLDINGS
with tab2:
    st.subheader("Performance odierna delle principali componenti Tech/US")
    if not df_tech.empty:
        c1, c2 = st.columns([3, 2])
        with c1:
            fig_tech = px.bar(
                df_tech.sort_values(by="Variazione 1G (%)"),
                x="Variazione 1G (%)",
                y="Nome",
                orientation='h',
                color="Variazione 1G (%)",
                color_continuous_scale=["#FF4B4B", "#30363d", "#00CC66"]
            )
            fig_tech.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig_tech, use_container_width=True)
        with c2:
            st.dataframe(df_tech, hide_index=True, use_container_width=True)

# TAB 3: DEFENSE HOLDINGS
with tab3:
    st.subheader("Hedge Geopolitico: Titoli della Difesa nel VWCE")
    if not df_defense.empty:
        c1, c2 = st.columns([3, 2])
        with c1:
            fig_def = px.bar(
                df_defense.sort_values(by="Variazione 1G (%)"),
                x="Variazione 1G (%)",
                y="Nome",
                orientation='h',
                color="Variazione 1G (%)",
                color_continuous_scale=["#FF4B4B", "#30363d", "#00CC66"]
            )
            fig_def.update_layout(template="plotly_dark", height=400)
            st.plotly_chart(fig_def, use_container_width=True)
        with c2:
            st.dataframe(df_defense, hide_index=True, use_container_width=True)

# TAB 4: MACRO
with tab4:
    st.subheader("Indicatori di Rischio e Contesto Macroeconomico")
    if not df_macro.empty:
        st.dataframe(df_macro, hide_index=True, use_container_width=True)

# TAB 5: SIMULATORE PAC
with tab5:
    st.subheader("Simulazione Crescita Capitale (PAC)")
    months = pac_years * 12
    rate = expected_return / 100 / 12
    
    dates = [datetime.now() + timedelta(days=30*i) for i in range(months)]
    invested = [pac_monthly * (i+1) for i in range(months)]
    future_val = [pac_monthly * (((1 + rate)**(i+1) - 1) / rate) * (1 + rate) for i in range(months)]
    
    df_pac = pd.DataFrame({"Data": dates, "Capitale Versato": invested, "Valore Stimato": future_val})
    
    fig_pac = go.Figure()
    fig_pac.add_trace(go.Scatter(x=df_pac["Data"], y=df_pac["Capitale Versato"], name="Versato", line=dict(color='#888888')))
    fig_pac.add_trace(go.Scatter(x=df_pac["Data"], y=df_pac["Valore Stimato"], name="Capitale con Interessi", line=dict(color='#00CC66', width=3)))
    fig_pac.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_pac, use_container_width=True)
    
    st.success(f"Totale Versato: **{invested[-1]:,.2f} €** | Valore Finale Stimato: **{future_val[-1]:,.2f} €** (Interessi Maturati: **{future_val[-1]-invested[-1]:,.2f} €**)")

# ---------------------------------------------------------
# NOTIZIE E FEED GEOPOLITICO (IN BASSO)
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📰 Market & Geopolitical News Feed")
if news_vwce:
    for n in news_vwce[:5]:
        st.markdown(f"🔹 **[{n.get('title')}]({n.get('link')})** — *{n.get('publisher')}*")
else:
    st.info("I feed di notizie di Yahoo Finance verranno aggiornati all'apertura dei mercati.")
