import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ---------------------------------------------------------
# CONFIGURAZIONE STILE AVANZATO TERMINALE
# ---------------------------------------------------------
st.set_page_config(
    page_title="VWCE Pro Financial Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS per rispecchiare il layout del Terminale Finanziario
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] { color: #8b949e; font-size: 0.85rem; font-weight: 600; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; color: #58a6ff; }
    .status-card {
        background-color: #161b22;
        border-left: 4px solid #238636;
        padding: 12px 20px;
        border-radius: 6px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATI E TICKER
# ---------------------------------------------------------
VWCE_TICKER = "VWCE.DE"

HOLDINGS_DATA = [
    {"Azienda": "Apple Inc.", "Ticker": "AAPL", "Settore": "Tecnologia", "Peso": 4.5},
    {"Azienda": "Microsoft Corp.", "Ticker": "MSFT", "Settore": "Tecnologia", "Peso": 3.6},
    {"Azienda": "NVIDIA Corp.", "Ticker": "NVDA", "Settore": "Tecnologia", "Peso": 3.2},
    {"Azienda": "Amazon.com", "Ticker": "AMZN", "Settore": "Beni di Consumo", "Peso": 2.3},
    {"Azienda": "Alphabet Inc.", "Ticker": "GOOGL", "Settore": "Tecnologia", "Peso": 2.1},
    {"Azienda": "TSMC", "Ticker": "TSM", "Settore": "Tecnologia", "Peso": 1.8},
    {"Azienda": "Meta Platforms", "Ticker": "META", "Settore": "Tecnologia", "Peso": 1.5},
    {"Azienda": "Tesla Inc.", "Ticker": "TSLA", "Settore": "Beni di Consumo", "Peso": 1.0},
    {"Azienda": "Lockheed Martin", "Ticker": "LMT", "Settore": "Difesa & Industriale", "Peso": 0.3},
    {"Azienda": "IBM", "Ticker": "IBM", "Settore": "Tecnologia", "Peso": 0.2}
]

@st.cache_data(ttl=900)
def fetch_market_data():
    etf = yf.Ticker(VWCE_TICKER)
    hist = etf.history(period="1y")
    
    # Dati live delle holding
    holdings_df = pd.DataFrame(HOLDINGS_DATA)
    perf_list = []
    for symbol in holdings_df['Ticker']:
        try:
            t = yf.Ticker(symbol)
            h = t.history(period="2d")
            if len(h) >= 2:
                c = h['Close'].iloc[-1]
                p = h['Close'].iloc[-2]
                perf_list.append(((c - p) / p) * 100)
            else:
                perf_list.append(0.0)
        except Exception:
            perf_list.append(0.0)
            
    holdings_df['Variazione %'] = [round(x, 2) for x in perf_list]
    return hist, holdings_df, etf.news

hist_etf, df_holdings, news_list = fetch_market_data()

# ---------------------------------------------------------
# HEADER DEL TERMINALE
# ---------------------------------------------------------
st.title("⚡ VWCE Interactive Financial Terminal")
st.markdown("""
<div class="status-card">
    <b>Stato del Sistema:</b> Connessione Live ai Mercati attiva | Aggiornato automaticamente ad ogni sessione di Borsa.
</div>
""", unsafe_allow_html=True)

if not hist_etf.empty:
    price = hist_etf['Close'].iloc[-1]
    prev = hist_etf['Close'].iloc[-2]
    chg = price - prev
    pct = (chg / prev) * 100
    
    returns = hist_etf['Close'].pct_change().dropna()
    vol = returns.std() * np.sqrt(252) * 100
    sharpe = (returns.mean() * 252) / (returns.std() * np.sqrt(252))

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Prezzo VWCE", f"{price:.2f} €", f"{chg:+.2f} € ({pct:+.2f}%)")
    c2.metric("Volatilità Annua", f"{vol:.2f}%")
    c3.metric("Sharpe Ratio", f"{sharpe:.2f}")
    c4.metric("Massimo 52 Settimane", f"{hist_etf['High'].max():.2f} €")
    c5.metric("Minimo 52 Settimane", f"{hist_etf['Low'].min():.2f} €")

st.markdown("---")

# ---------------------------------------------------------
# TREEMAP INTERATTIVA & TOP HOLDINGS (COME NELL'ANTEPRIMA)
# ---------------------------------------------------------
st.subheader("🗺️ Treemap Interattiva del Portafoglio & Impatto Giornaliero")
st.caption("Dimensioni = Peso nel VWCE (%) | Colore = Andamento percentuale della seduta odierna")

fig_tree = px.treemap(
    df_holdings,
    path=[px.Constant("VWCE Global"), 'Settore', 'Azienda'],
    values='Peso',
    color='Variazione %',
    color_continuous_scale=['#ff4b4b', '#1f2937', '#00c853'],
    color_continuous_midpoint=0
)
fig_tree.update_traces(
    hovertemplate='<b>%{label}</b><br>Peso nel fondo: %{value}%<br>Variazione Oggi: %{color:.2f}%',
    textinfo="label+value+percent parent"
)
fig_tree.update_layout(template="plotly_dark", height=480, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig_tree, use_container_width=True)

# ---------------------------------------------------------
# ANALISI STORICA & RISCHIO GEOPOLITICO
# ---------------------------------------------------------
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📈 Performance Storica & Medie Mobili")
    hist_etf['SMA50'] = hist_etf['Close'].rolling(50).mean()
    hist_etf['SMA200'] = hist_etf['Close'].rolling(200).mean()
    
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=hist_etf.index, y=hist_etf['Close'], name='Prezzo VWCE', line=dict(color='#58a6ff', width=2)))
    fig_line.add_trace(go.Scatter(x=hist_etf.index, y=hist_etf['SMA50'], name='Media 50gg', line=dict(color='#d29922', width=1)))
    fig_line.add_trace(go.Scatter(x=hist_etf.index, y=hist_etf['SMA200'], name='Media 200gg', line=dict(color='#f85149', width=1)))
    fig_line.update_layout(template="plotly_dark", height=400, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_line, use_container_width=True)

with col_right:
    st.subheader("🛡️ Matrice di Impatto Geopolitico")
    geo_df = pd.DataFrame([
        {"Evento Geopolitico": "Tensioni Medio Oriente / Petrolio", "Settore Impattato": "Energia / Difesa", "Impatto VWCE": "Moderato Positive (+)"},
        {"Evento Geopolitico": "Restrizioni US/Cina Semiconduttori", "Settore Impattato": "Tech / Chip", "Impatto VWCE": "Alta Volatilità (±)"},
        {"Evento Geopolitico": "Spesa Riarmo Unione Europea", "Settore Impattato": "Industriale / Difesa", "Impatto VWCE": "Copertura Rischio (+)"},
        {"Evento Geopolitico": "Politica Tassi Banche Centrali", "Settore Impattato": "Finanza / Reits", "Impatto VWCE": "Neutro / Stabile (=)"}
    ])
    st.dataframe(geo_df, hide_index=True, use_container_width=True, height=380)

# ---------------------------------------------------------
# FEED NOTIZIE & GEOPOLITICA
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📰 Notizie ed Eventi Correlati al Mercato Globale")
if news_list:
    for item in news_list[:5]:
        title = item.get('title', 'Nessun titolo')
        link = item.get('link', '#')
        publisher = item.get('publisher', 'Fonte sconosciuta')
        st.markdown(f"🔹 **[{title}]({link})** — *{publisher}*")
