import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import time
import re

# 1. Pagina Configuratie
st.set_page_config(page_title="AI Trader Pro - Live", layout="wide")

# 2. Geavanceerde CSS voor Contrast en Layout
st.markdown("""
    <style>
    /* Hoofdpagina en Sidebar */
    .stApp { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #0a0a0a !important; border-right: 1px solid #333 !important; }
    
    /* Tekst kleuren */
    h1, h2, h3, p, label, span { color: #ffffff !important; }
    
    /* KNOPPEN CONTRAST: Duidelijk zichtbaar maken */
    .stButton>button {
        background-color: #222222 !important;
        color: #ffffff !important;
        border: 1px solid #444444 !important;
        border-radius: 5px;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #333333 !important;
        border-color: #39d353 !important;
        color: #39d353 !important;
    }

    /* Input velden contrast */
    .stTextInput>div>div>input {
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }

    /* Tabel layout verbetering */
    .stTable { 
        background-color: #000000 !important; 
        border: 1px solid #333 !important;
    }
    
    /* Metrics kleur forceren */
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Watchlist Management (Lijst fix)
if 'watchlist' not in st.session_state or not isinstance(st.session_state.watchlist, list):
    st.session_state.watchlist = ["AAPL", "NVDA", "TSLA"]

# 4. AI-Analyse Functie
def perform_ai_analysis(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).history(period="100d")
        if data.empty: return None
        
        curr_p = float(data['Close'].iloc[-1])
        prev_p = float(data['Close'].iloc[-2])
        change = ((curr_p / prev_p) - 1) * 100
        
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
            "Prijs": f"${curr_p:.2f}",
            "Change %": f"{change:+.2f}%",
            "Score": f"{ensemble}%",
            "Swing": round(swing_score, 1),
            "Advies": f"{ico} {rec}",
            "Kleur": col
        }
    except:
        return None

# 5. Sidebar Layout
with st.sidebar:
    st.header("📋 Watchlist Beheer")
    st.markdown("---")
    
    multi_input = st.text_input("Nieuwe tickers (komma gescheiden)", placeholder="bijv: META, AMZN, BTC-USD")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Toevoegen"):
            if multi_input:
                new_list = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
                st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new_list))
                st.rerun()
    with col2:
        if st.button("Lijst Wissen"):
            st.session_state.watchlist = []
            st.rerun()
    
    st.markdown("---")
    st.caption("Live updates elke 10 seconden.")

# 6. Hoofd Dashboard (Live Fragment)
st.title("🏹 AI Strategy Terminal")

@st.fragment(run_every=10)
def show_dashboard():
    if not st.session_state.watchlist:
        st.info("De watchlist is momenteel leeg. Voeg tickers toe in de sidebar.")
        return

    # Header met tijdstempel
    st.write(f"⏱️ **Live Markt Update:** {time.strftime('%H:%M:%S')}")
    
    analysis_results = []
    for t in st.session_state.watchlist:
        res = perform_ai_analysis(t)
        if res:
            analysis_results.append(res)
    
    if analysis_results:
        # Tabel weergeven
        df = pd.DataFrame(analysis_results)
        # Verwijder kleur kolom uit de tabel weergave
        display_df = df.drop(columns=['Kleur'])
        st.table(display_df)
        
        # Grid layout voor visuele status
        st.subheader("🔥 Top Focus")
        cols = st.columns(min(len(analysis_results), 4))
        for i, item in enumerate(analysis_results[:8]):
            with cols[i % 4]:
                st.markdown(f"""
                    <div style="padding:10px; border-radius:8px; background-color:#111; border: 1px solid {item['Kleur']}; margin-bottom:10px;">
                        <h4 style="margin:0; color:{item['Kleur']} !important;">{item['Ticker']}</h4>
                        <p style="font-size:1.2em; font-weight:bold; margin:0;">{item['Prijs']}</p>
                        <p style="margin:0; font-size:0.9em;">Score: {item['Score']}</p>
                    </div>
                """, unsafe_allow_html=True)

show_dashboard()























