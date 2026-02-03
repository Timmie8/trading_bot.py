import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
import time

# 1. Pagina configuratie
st.set_page_config(page_title="AI Trader Pro", layout="wide")

# INITIALISEER WATCHLIST (Session State)
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA"] # Standaard tickers

# 2. Hulpfuncties voor Analyse
def get_analysis(ticker_symbol):
    """Haalt data op en berekent scores voor één specifiek aandeel."""
    try:
        data = yf.Ticker(ticker_symbol).history(period="100d")
        if data.empty: return None
        
        curr_p = float(data['Close'].iloc[-1])
        prev_p = float(data['Close'].iloc[-2])
        change = ((curr_p / prev_p) - 1) * 100
        
        # AI Trend (Linear Regression)
        y = data['Close'].values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        
        score = 70 + (10 if pred > curr_p else -10)
        rec = "BUY" if score > 75 else "HOLD"
        col = "#39d353" if rec == "BUY" else "#d29922"
        
        return {
            "Ticker": ticker_symbol,
            "Prijs": f"${curr_p:.2f}",
            "Change": f"{change:+.2f}%",
            "Advies": rec,
            "Kleur": col,
            "History": data['Close']
        }
    except:
        return None

# 3. Sidebar voor invoer
with st.sidebar:
    st.header("⚙️ Instellingen")
    
    # Mogelijkheid om meerdere aandelen tegelijk in te voeren
    input_tickers = st.text_area("Voer tickers in (scheid met komma of spatie)", 
                                 value=", ".join(st.session_state.watchlist))
    
    if st.button("Watchlist Bijwerken"):
        # Schoon de input op: splits op komma, verwijder spaties, maak hoofdletters
        new_list = [t.strip().upper() for t in re.split(r'[,\s]+', input_tickers) if t.strip()]
        st.session_state.watchlist = list(dict.fromkeys(new_list)) # Verwijder dubbelen
        st.rerun()

    st.write("---")
    st.write("⏱️ *De pagina ververst elke 30 seconden automatisch voor live prijzen.*")

# 4. Hoofd Dashboard (De "Live" Watchlist)
st.title("🏹 AI Strategy Terminal")

# We maken een grid/tabel voor de live watchlist bovenin
if st.session_state.watchlist:
    st.subheader("📋 Live Overzicht")
    
    # Verzamel data voor alle tickers
    live_results = []
    for t in st.session_state.watchlist:
        res = get_analysis(t)
        if res:
            live_results.append(res)
    
    if live_results:
        # Maak een mooie tabel van de huidige watchlist data
        df_display = pd.DataFrame(live_results).drop(columns=['History', 'Kleur'])
        st.table(df_display)
        
        # Toon gedetailleerde kaarten per aandeel
        st.write("---")
        cols = st.columns(len(live_results))
        for i, item in enumerate(live_results):
            with cols[i % len(cols)]:
                st.markdown(f"""
                    <div style="padding:10px; border-radius:10px; background-color:#161b22; border-left: 5px solid {item['Kleur']};">
                        <h4 style="margin:0;">{item['Ticker']}</h4>
                        <p style="font-size:1.2em; font-weight:bold; margin:0;">{item['Prijs']}</p>
                        <p style="color:{item['Kleur']}; margin:0;">{item['Advies']} ({item['Change']})</p>
                    </div>
                """, unsafe_allow_html=True)

# 5. Automatische Refresh Logica
# Dit zorgt ervoor dat de watchlist 'live' blijft
time.sleep(30)
st.rerun()




















