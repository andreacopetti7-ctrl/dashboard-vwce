import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ---------------------------------------------------------
# SETUP PAGINA & CSS ULTRA-PROFESSIONALE (BLOOMBERG/TRADINGVIEW STYLE)
# ---------------------------------------------------------
st.set_page_config(
    page_title="VWCE Bloomberg-Style Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Reset & Dark Theme Base */
    .stApp {
        background-color: #080a0f !important;
        color: #d1d5db !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Header Personalizzato */
    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #111827;
        padding: 10px 20px;
        border-radius: 8px;
        border: 1px solid #1f2937;
        margin-bottom: 15px;
    }
    .terminal-title {
        font-size: 1.3rem;
        font-weight: 800;
        color: #38bdf8;
        letter-spacing: 0.5px;
    }
    .live-badge {
        background-color: #064e3b;
        color: #34d399;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid #059669;
    }

    /* Cards e Metriche ad Alta Densità */
    div[data-testid="stMetric"] {
        background: #111827 !important;
        border: 1px solid #1f2937 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.4);
    }
    div[data-testid="stMetricLabel"] {
        color: #9ca3af !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        color: #f3f4f6 !important;
    }
    
    /* Riduzione spaziature bianche di Streamlit */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 98% !important;
    }
    
    /* Stile Tab */
    button[data-baseweb="tab"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #9ca3af !important;
        background-color: transparent !important;
    }
    button[aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom-color: #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATI & TICKER
# ---------------------------------------------------------
VWCE_TICKER = "VWCE.DE"

HOLDINGS_DATA = [
    {"Azienda": "Apple", "Ticker": "AAPL", "Settore": "Tech", "Peso": 4.5},
    {"Azienda": "Microsoft", "Ticker": "MSFT", "Settore": "Tech", "Peso": 3.6},
    {"Azienda": "NVIDIA", "Ticker": "NVDA", "Settore": "Tech", "Peso": 3.2},
    {"Azienda": "Amazon", "Ticker": "AMZN", "Settore": "Consumi", "Peso": 2.3},
    {"Azienda": "Alphabet", "Ticker": "GOOGL", "Settore": "Tech", "Peso": 2.1},
    {"Azienda": "TSMC", "Ticker": "TSM", "Settore": "Tech", "Peso": 1.8},
    {"Azienda": "Meta", "Ticker": "META", "Settore": "Tech", "Peso": 1.5},
    {"Azienda": "Tesla", "Ticker": "TSLA", "Settore": "Consumi", "Peso": 1.0},
    {"Azienda": "Broadcom", "Ticker": "AVGO", "Settore": "Tech", "Peso": 0.9},
    {"Azienda": "Lockheed M.", "Ticker": "LMT", "Settore": "Difesa", "Peso": 0.3},
    {"Azienda": "Rheinmetall", "Ticker": "RHM.DE", "Settore": "Difesa", "Peso": 0.2}
]

@st.cache_data(ttl=600)
def get_terminal_data():
    etf = yf.Ticker(VWCE_TICKER)
    hist = etf.history(period="1y")
    
    # Prende variazioni live delle holding
    df_h = pd.DataFrame(HOLDINGS_DATA)
    changes = []
    prices = []
    for t_sym in df_h['Ticker']:
        try:
            h = yf.Ticker(t_sym).history(period="2d")
            if len(h) >= 2:
                c, p = h['Close'].iloc[-1], h['Close'].iloc[-2]
                prices.append(round(c, 2))
                changes.append(round(((c - p) / p) * 100, 2))
            else:
                prices.append(0.0)
                changes.append(0.0)
        except Exception:
            prices.append(0.0)
            changes.append(0.0)
            
    df_h['Prezzo'] = prices
    df_h['Var 1G (%)'] = changes
    return hist, df_h, etf.news

hist_etf, df_holdings, news_list = get_terminal_data()

# ---------------------------------------------------------
# TERMINAL HEADER BAR
# ---------------------------------------------------------
st.markdown(f"""
<div class="terminal-header">
    <div class="terminal-title">⚡ VWCE PRO FINANCIAL TERMINAL</div>
    <div style="font-size: 0.8rem; color: #9ca3af;">XETRA: VWCE.DE | ISIN: IE00BK5BQT80</div>
    <div class="live-badge">● LIVE DATA STREAM</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# METRICHE PRINCIPALI IN PRIMO PIANO
# ---------------------------------------------------------
if not hist_etf.empty:
    price = hist_etf['Close'].iloc[-1]
    prev = hist_etf['Close'].iloc[-2]
    chg = price - prev
    pct = (chg / prev) * 100
    
    ret = hist_etf['Close'].pct_change().dropna()
    vol = ret.std() * np.sqrt(252) * 100
    sharpe = (ret.mean() * 252) / (ret.std() * np.sqrt(252))

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Prezzo", f"{price:.2f} €", f"{chg:+.2f} € ({pct:+.2f}%)")
    c2.metric("Volatilità (1A)", f"{vol:.2f}%")
    c3.metric("Sharpe Ratio", f"{sharpe:.2f}")
    c4.metric("Max 52W", f"{hist_etf['High'].max():.2f} €")
    c5.metric("Min 52W", f"{hist_etf['Low'].min():.2f} €")
    c6.metric("Volumi Oggi", f"{int(hist_etf['Volume'].iloc[-1]):,}")

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# LAYOUT PRINCIPALE A 2 COLONNE
# ---------------------------------------------------------
col_main, col_side = st.columns([7, 3])

with col_main:
    # Grafico Candele / Linea avanzato
    st.markdown("##### 📈 Grafico di Borsa Interattivo")
    
    hist_etf['SMA50'] = hist_etf['Close'].rolling(50).mean()
    hist_etf['SMA200'] = hist_etf['Close'].rolling(200).mean()
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=hist_etf.index, open=hist_etf['Open'], high=hist_etf['High'],
        low=hist_etf['Low'], close=hist_etf['Close'], name='VWCE Price'
    ))
    fig.add_trace(go.Scatter(x=hist_etf.index, y=hist_etf['SMA50'], name='SMA 50', line=dict(color='#f59e0b', width=1.5)))
    fig.add_trace(go.Scatter(x=hist_etf.index, y=hist_etf['SMA200'], name='SMA 200', line=dict(color='#ef4444', width=1.5)))
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        height=420,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Treemap Densità Portafoglio
    st.markdown("##### 🗺️ Mappa ad Albero (Treemap) Costituenti & Impatto")
    fig_tree = px.treemap(
        df_holdings,
        path=[px.Constant("VWCE Holdings"), 'Settore', 'Azienda'],
        values='Peso',
        color='Var 1G (%)',
        color_continuous_scale=['#ef4444', '#1f2937', '#10b981'],
        color_continuous_midpoint=0
    )
    fig_tree.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        height=320,
        margin=dict(l=5, r=5, t=5, b=5)
    )
    st.plotly_chart(fig_tree, use_container_width=True)

with col_side:
    # Tabella Holding Compatta
    st.markdown("##### 🏢 Top Holdings Live")
    st.dataframe(
        df_holdings[['Azienda', 'Peso', 'Var 1G (%)']],
        hide_index=True,
        use_container_width=True,
        height=360
    )
    
    # Rischio Geopolitico
    st.markdown("##### 🛡️ Matrice Impatto Geopolitico")
    geo_data = pd.DataFrame([
        {"Evento": "Tensioni Medio Oriente", "Impatto": "Petrolio / Difesa (+)"},
        {"Evento": "Restrizioni US/Cina Chip", "Impatto": "Tech / Semiconduttori (±)"},
        {"Evento": "Spesa Riarmo UE", "Impatto": "Industria Difesa (+)"},
        {"Evento": "Politica Tassi Fed/BCE", "Impatto": "Banche / Reits (=)"}
    ])
    st.dataframe(geo_data, hide_index=True, use_container_width=True, height=220)

# ---------------------------------------------------------
# FEED NOTIZIE IN BASSO
# ---------------------------------------------------------
st.markdown("---")
st.markdown("##### 📰 Live Market & Geopolitical News Feed")
if news_list:
    cols_news = st.columns(3)
    for idx, item in enumerate(news_list[:3]):
        with cols_news[idx]:
            st.markdown(f"""
            <div style="background: #111827; padding: 12px; border-radius: 6px; border: 1px solid #1f2937; height: 100%;">
                <div style="font-size: 0.75rem; color: #38bdf8;">{item.get('publisher', 'News')}</div>
                <div style="font-weight: 600; font-size: 0.85rem; margin-top: 4px;">
                    <a href="{item.get('link', '#')}" target="_blank" style="color: #f3f4f6; text-decoration: none;">{item.get('title', 'Titolo non disponibile')}</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
