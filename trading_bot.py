import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import time
import re

# 1. Pagina Configuratie & Harde Black-Mode Styling
st.set_page_config(page_title="AI Trader Pro - Live", layout="wide")

st.markdown("""
    <style>
    .stApp, [data-testid="stAppViewContainer"] { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
    h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown { color: #ffffff !important; }
    .stTable { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. FIX VOOR TYPEERROR: Zorg dat watchlist ALTIJD een lijst is
if 'watchlist' not in st.session_state or not isinstance(st.session_state.watchlist, list):
    st.session_state.watchlist = ["AAPL", "NVDA"]

# 3. AI-Analyse Functie
def perform_ai_analysis(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).history(period="100d")
        if data.empty: return None
        
        curr_p = float(data['Close'].iloc[-1])
        prev_p = float(data['Close'].iloc[-2])
        change = ((curr_p / prev_p) - 1) * 100
        
        # AI Trend Voorspelling
        y = data['Close'].values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        
        ensemble = int(72 + (12 if pred > curr_p else -8))
        vola = data['Close'].pct_change().tail(14).std() * 100
        swing_score = 50 + (change * 6) - (vola * 4)
        
        if ensemble > 75 and swing_score > 58: rec, col, ico = "BUY", "#39d353", "🚀"
        elif ensemble < 65: rec, col, ico = "AVOID", "#f85149", "⚠️"
        else: rec, col, ico = "HOLD", "#d29922", "⏳"
        
        return {
            "Ticker": ticker_symbol,
            "Prijs": round(curr_p, 2),
            "Change %": round(change, 2),
            "Ensemble": ensemble,
            "Swing": round(swing_score, 1),
            "Status": f"{ico} {rec}",
            "Kleur": col
        }
    except:
        return None

# 4. Sidebar: Meerdere aandelen toevoegen
with st.sidebar:
    st.header("📋 Watchlist")
    multi_input = st.text_input("Voeg tickers toe (bijv: AAPL,TSLA,NVDA)", key="input")
    
    if st.button("Bijwerken"):
        if multi_input:
            # Maak een lijst van de input
            new_list = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
            # Voeg samen en verwijder duplicaten
            current_list = st.session_state.watchlist
            st.session_state.watchlist = list(dict.fromkeys(current_list + new_list))
            st.rerun()
            
    if st.button("Lijst wissen"):
        st.session_state.watchlist = []
        st.rerun()

# 5. Dashboard (Live fragment voor updates zonder refresh)
st.title("🏹 AI Strategy Terminal")

@st.fragment(run_every=10)
def show_dashboard():
    if not st.session_state.watchlist:
        st.info("De watchlist is leeg.")
        return

    st.write(f"⏱️ Live Update: {time.strftime('%H:%M:%S')}")
    
    analysis_results = []
    for t in st.session_state.watchlist:
        res = perform_ai_analysis(t)
        if res:
            analysis_results.append(res)
    
    if analysis_results:
        df = pd.DataFrame(analysis_results)
        # Toon de tabel met alle cruciale scores
        st.table(df[['Ticker', 'Prijs', 'Change %', 'Ensemble', 'Swing', 'Status']])
        
        # Metrics voor snelle blik
        cols = st.columns(min(len(analysis_results), 4))
        for i, item in enumerate(analysis_results[:8]): # Max 8 metrics tonen
            with cols[i % 4]:
                st.metric(item['Ticker'], f"${item['Prijs']}", f"{item['Change %']}%")

show_dashboard()






















