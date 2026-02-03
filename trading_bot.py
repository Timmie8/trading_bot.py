import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
import time

# 1. Pagina Configuratie
st.set_page_config(page_title="AI Trader Pro - Live", layout="wide")

# 2. Harde Reset Styling (Zwart scherm forceren)
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
    /* Knoppen contrast */
    .stButton>button { 
        background-color: #222 !important; color: white !important; 
        border: 1px solid #444 !important; font-weight: bold;
    }
    .stButton>button:hover { border-color: #39d353 !important; color: #39d353 !important; }
    /* Input tekst wit maken */
    input { background-color: #111 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Watchlist Geheugen (Lijst formaat)
if 'watchlist' not in st.session_state or not isinstance(st.session_state.watchlist, list):
    st.session_state.watchlist = ["AAPL", "TSLA"]

# 4. AI Logica (Exacte kopie van jouw basis)
def run_full_analysis(ticker):
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if data.empty: return None
        curr_p = float(data['Close'].iloc[-1])
        prev_p = float(data['Close'].iloc[-2])
        change = ((curr_p / prev_p) - 1) * 100
        
        y = data['Close'].values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        
        ensemble = int(72 + (12 if pred > curr_p else -8))
        lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
        vola = data['Close'].pct_change().tail(14).std() * 100
        swing = 50 + (change * 6) - (vola * 4)
        
        if (ensemble > 75 or lstm > 70) and swing > 58: rec, col = "BUY", "#39d353"
        elif ensemble < 65: rec, col = "AVOID", "#f85149"
        else: rec, col = "HOLD", "#d29922"
        
        return {
            "Ticker": ticker, "Prijs": curr_p, "Change": change,
            "Ensemble": ensemble, "LSTM": lstm, "Swing": round(swing, 1),
            "Status": rec, "Kleur": col
        }
    except: return None

# 5. Sidebar
with st.sidebar:
    st.header("📋 Watchlist")
    multi_input = st.text_area("Voeg tickers toe (komma gescheiden)", placeholder="NVDA, MSFT, BTC-USD")
    if st.button("Toevoegen"):
        new = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
        st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new))
        st.rerun()
    if st.button("Lijst Wissen"):
        st.session_state.watchlist = []
        st.rerun()

# 6. Dashboard
st.title("🏹 AI Strategy Terminal")

# DIRECTE SCAN SECTIE
st.subheader("🔍 Directe Scan")
scan_ticker = st.text_input("Voer ticker in voor snelle analyse", "AAPL").upper()
if scan_ticker:
    s = run_full_analysis(scan_ticker)
    if s:
        # Groene rand als Status BUY is
        border_color = s['Kleur'] if s['Status'] == "BUY" else "#333"
        st.markdown(f"""
            <div style="border: 2px solid {border_color}; padding: 20px; border-radius: 10px; background-color: #111;">
                <h2 style="color:{s['Kleur']} !important; margin:0;">{s['Status']}: {s['Ticker']}</h2>
                <h3 style="margin:0;">${s['Prijs']:.2f} ({s['Change']:+.2f}%)</h3>
                <p>AI Score: {s['Ensemble']}% | LSTM: {s['LSTM']}% | Swing: {s['Swing']}</p>
            </div>
        """, unsafe_allow_html=True)

st.write("---")

# LIVE WATCHLIST SECTIE
@st.fragment(run_every=10)
def show_watchlist():
    st.subheader("🔄 Live Watchlist (Update elke 10s)")
    if not st.session_state.watchlist:
        st.info("Lijst is leeg.")
        return

    # Tabel Koppen
    st.markdown("""
        <div style="display: flex; font-weight: bold; border-bottom: 2px solid #333; padding-bottom: 5px; color: #39d353;">
            <div style="width: 20%;">Ticker</div><div style="width: 20%;">Prijs</div>
            <div style="width: 20%;">Score</div><div style="width: 20%;">Swing</div>
            <div style="width: 20%;">Status</div>
        </div>
    """, unsafe_allow_html=True)

    for t in st.session_state.watchlist:
        data = run_full_analysis(t)
        if data:
            # Groene rand forceren bij BUY
            row_style = f"border: 2px solid #39d353; background-color: rgba(57, 211, 83, 0.1);" if data['Status'] == "BUY" else "border: 1px solid #222;"
            
            st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 10px; margin-top: 5px; border-radius: 5px; {row_style}">
                    <div style="width: 20%;"><b>{data['Ticker']}</b></div>
                    <div style="width: 20%;">${data['Prijs']:.2f}</div>
                    <div style="width: 20%;">{data['Ensemble']}%</div>
                    <div style="width: 20%;">{data['Swing']}</div>
                    <div style="width: 20%; color:{data['Kleur']}; font-weight:bold;">{data['Status']}</div>
                </div>
            """, unsafe_allow_html=True)

show_watchlist()























