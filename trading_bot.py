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
    /* Styling voor de score-kaarten */
    .report-card { 
        padding: 15px; border-radius: 10px; background-color: #111; 
        border-left: 5px solid #444; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Geheugen voor de Watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "NVDA"]

# 3. De AI-Analyse Functie (Teruggehaald uit je originele code)
def perform_ai_analysis(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).history(period="100d")
        if data.empty: return None
        
        curr_p = float(data['Close'].iloc[-1])
        prev_p = float(data['Close'].iloc[-2])
        change = ((curr_p / prev_p) - 1) * 100
        
        # AI Trend Voorspelling (Linear Regression)
        y = data['Close'].values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        
        # Berekeningen voor de scores
        ensemble = int(72 + (12 if pred > curr_p else -8))
        vola = data['Close'].pct_change().tail(14).std() * 100
        swing_score = 50 + (change * 6) - (vola * 4)
        
        # Bepaal status
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

# 4. Sidebar: Meerdere aandelen toevoegen via komma
with st.sidebar:
    st.header("📋 Watchlist")
    multi_input = st.text_input("Voeg tickers toe (bijv: AAPL,TSLA,BTC-USD)", key="input")
    
    if st.button("Bijwerken"):
        if multi_input:
            new_list = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
            st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new_list))
            st.rerun()
            
    if st.button("Lijst wissen"):
        st.session_state.watchlist = []
        st.rerun()

# 5. Hoofd Dashboard (Live Fragment)
st.title("🏹 AI Strategy Terminal")

@st.fragment(run_every=10)
def show_dashboard():
    if not st.session_state.watchlist:
        st.info("Voeg tickers toe in de sidebar.")
        return

    st.write(f"⏱️ Laatste Update: {time.strftime('%H:%M:%S')}")
    
    analysis_results = []
    for t in st.session_state.watchlist:
        res = perform_ai_analysis(t)
        if res:
            analysis_results.append(res)
    
    if analysis_results:
        # Maak een DataFrame voor de tabel
        df = pd.DataFrame(analysis_results)
        
        # Toon de cruciale tabel met alle scores
        st.table(df[['Ticker', 'Prijs', 'Change %', 'Ensemble', 'Swing', 'Status']])
        
        # Visuele kaarten
        st.write("---")
        cols = st.columns(min(len(analysis_results), 4))
        for i, item in enumerate(analysis_results):
            with cols[i % 4]:
                st.markdown(f"""
                    <div style="padding:15px; border-radius:10px; background-color:#111; border-top: 4px solid {item['Kleur']};">
                        <h3 style="margin:0;">{item['Ticker']}</h3>
                        <p style="font-size:1.5em; font-weight:bold; margin:0;">${item['Prijs']}</p>
                        <p style="color:{item['Kleur']};">Score: {item['Ensemble']}% | {item['Status']}</p>
                    </div>
                """, unsafe_allow_html=True)

# Start de live weergave
show_dashboard()





















