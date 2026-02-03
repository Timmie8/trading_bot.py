import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
import time
import os

# --- PERSISTENTIE LOGICA ---
def save_watchlist(watchlist):
    with open("watchlist_data.txt", "w") as f:
        f.write(",".join(watchlist))

def load_watchlist():
    if os.path.exists("watchlist_data.txt"):
        with open("watchlist_data.txt", "r") as f:
            data = f.read().strip()
            return data.split(",") if data else []
    return ["AAPL", "TSLA", "NVDA"]

# 1. Pagina Setup
st.set_page_config(page_title="AI Trader Pro", layout="wide")

# 2. Harde CSS voor Zwarte Layout
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
    h1, h2, h3, h4, p, label, span { color: #ffffff !important; }
    .stButton>button { background-color: #222 !important; color: white !important; border: 1px solid #444 !important; }
    input, textarea { background-color: #111 !important; color: white !important; border: 1px solid #333 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Watchlist Laden
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = load_watchlist()

# 4. Scrapers & AI Berekeningen
def get_earnings_date(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        return match.group(1).strip().split('-')[0].strip() if match else "N/A"
    except: return "N/A"

def run_analysis(ticker):
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if data.empty: return None
        curr_p = float(data['Close'].iloc[-1])
        prev_p = float(data['Close'].iloc[-2])
        change = ((curr_p / prev_p) - 1) * 100
        
        # --- AI BEREKENINGEN (GELIJK AAN BASISCODE) ---
        y = data['Close'].values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        
        ensemble = int(72 + (12 if pred > curr_p else -8))
        # LSTM simulatie op basis van momentum
        lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
        vola = data['Close'].pct_change().tail(14).std() * 100
        swing = round(50 + (change * 6) - (vola * 4), 1)
        earn = get_earnings_date(ticker)
        
        # --- BESLISSINGSLOGICA ---
        if (ensemble > 75 or lstm > 70) and swing > 58: 
            rec, col = "BUY", "#39d353"
        elif ensemble < 65: 
            rec, col = "AVOID", "#f85149"
        else: 
            rec, col = "HOLD", "#d29922"
        
        return {
            "T": ticker, "P": curr_p, "C": change, 
            "E": ensemble, "L": lstm, "S": swing, 
            "ST": rec, "COL": col, "EARN": earn
        }
    except: return None

# 5. Sidebar
with st.sidebar:
    st.header("📋 Watchlist")
    new_input = st.text_area("Voeg tickers toe (komma gescheiden)")
    if st.button("Toevoegen"):
        tickers = [t.strip().upper() for t in new_input.split(",") if t.strip()]
        st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + tickers))
        save_watchlist(st.session_state.watchlist)
        st.rerun()
    if st.button("Lijst Wissen"):
        st.session_state.watchlist = []
        save_watchlist([])
        st.rerun()

# 6. Dashboard
st.title("🏹 AI Strategy Terminal")

# DIRECTE SCAN
scan_ticker = st.text_input("Snel-scan Ticker", "AAPL").upper()
if scan_ticker:
    res = run_analysis(scan_ticker)
    if res:
        b_col = res['COL'] if res['ST'] == "BUY" else "#333"
        st.markdown(f"""
            <div style="border: 2px solid {b_col}; padding: 15px; border-radius: 10px; background-color: #111; margin-bottom: 20px;">
                <h2 style="color:{res['COL']}; margin:0;">{res['ST']}: {res['T']}</h2>
                <h3 style="margin:0;">${res['P']:.2f} ({res['C']:+.2f}%)</h3>
                <p style="margin:5px 0;">
                    <b>AI Ensemble:</b> {res['E']}% | <b>LSTM:</b> {res['L']}% | <b>Swing:</b> {res['S']}
                </p>
                <p style="margin:0; font-size: 0.9em;">📅 Next Earnings: <b>{res['EARN']}</b></p>
            </div>
        """, unsafe_allow_html=True)

# LIVE WATCHLIST (Update elke 10s)
@st.fragment(run_every=10)
def show_live_list():
    st.subheader("🔄 Live Watchlist Overzicht")
    if not st.session_state.watchlist:
        st.info("Geen aandelen in lijst.")
        return

    # Tabel Koppen
    st.markdown("""
        <div style="display: flex; font-weight: bold; border-bottom: 2px solid #444; padding: 10px; color: #39d353;">
            <div style="width: 12%;">Ticker</div><div style="width: 12%;">Prijs</div>
            <div style="width: 12%;">AI Score</div><div style="width: 12%;">LSTM</div>
            <div style="width: 12%;">Swing</div><div style="width: 15%;">Status</div>
            <div style="width: 25%;">Earnings</div>
        </div>
    """, unsafe_allow_html=True)

    for ticker in st.session_state.watchlist:
        d = run_analysis(ticker)
        if d:
            row_style = f"border: 2px solid #39d353; background-color: rgba(57, 211, 83, 0.1);" if d['ST'] == "BUY" else "border: 1px solid #222;"
            st.markdown(f"""
                <div style="display: flex; align-items: center; padding: 10px; margin-top: 5px; border-radius: 6px; {row_style}">
                    <div style="width: 12%; font-weight: bold;">{d['T']}</div>
                    <div style="width: 12%;">${d['P']:.2f}</div>
                    <div style="width: 12%;">{d['E']}%</div>
                    <div style="width: 12%;">{d['L']}%</div>
                    <div style="width: 12%;">{d['S']}</div>
                    <div style="width: 15%; color:{d['COL']}; font-weight:bold;">{d['ST']}</div>
                    <div style="width: 25%; font-size: 0.85em; color: #ccc;">{d['EARN']}</div>
                </div>
            """, unsafe_allow_html=True)

show_live_list()
























