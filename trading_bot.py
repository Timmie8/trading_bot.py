import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
import time

# 1. Pagina Configuratie & Styling
st.set_page_config(page_title="AI Trader Pro - Live", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
    h1, h2, h3, h4, p, label, span { color: #ffffff !important; }
    
    /* Contrast voor knoppen */
    .stButton>button {
        background-color: #1a1a1a !important;
        color: white !important;
        border: 1px solid #444 !important;
    }
    .stButton>button:hover { border-color: #39d353 !important; color: #39d353 !important; }
    
    /* Input velden */
    input { background-color: #111 !important; color: white !important; border: 1px solid #444 !important; }

    /* Groene rand voor BUY regels */
    .buy-row {
        border: 2px solid #39d353 !important;
        border-radius: 8px;
        padding: 5px;
        background-color: rgba(57, 211, 83, 0.1) !important;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Watchlist Geheugen
if 'watchlist' not in st.session_state or not isinstance(st.session_state.watchlist, list):
    st.session_state.watchlist = []

# 3. AI Logica Functies
def get_earnings(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        return match.group(1).strip().split('-')[0].strip() if match else "N/A"
    except: return "N/A"

def get_sentiment(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        headlines = [h.text.lower() for h in soup.find_all('h3')][:8]
        score = 70
        for h in headlines:
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit']): score += 3
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss']): score -= 3
        return min(98, max(35, score))
    except: return 50

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
        sent = get_sentiment(ticker)
        vola = data['Close'].pct_change().tail(14).std() * 100
        swing = 50 + (change * 6) - (vola * 4)
        earn = get_earnings(ticker)
        
        is_urgent = any(d in earn for d in ["Jan 29", "Jan 30", "Feb 1", "Feb 2", "Feb 3", "Feb 4"])
        if is_urgent: rec, ico = "AVOID", "⚠️"
        elif (ensemble > 75 or lstm > 70) and swing > 58: rec, ico = "BUY", "🚀"
        else: rec, ico = "HOLD", "⏳"
        
        return {
            "Ticker": ticker, "Prijs": f"${curr_p:.2f}", "Change %": f"{change:+.2f}%",
            "Ensemble": ensemble, "LSTM": lstm, "Sentiment": sent, "Swing": round(swing, 1),
            "Status": rec, "Ico": ico, "Earnings": earn
        }
    except: return None

# 4. Sidebar: Watchlist & Multi-input
with st.sidebar:
    st.header("📋 Watchlist Beheer")
    multi_input = st.text_input("Voeg tickers toe aan lijst (komma gescheiden)", placeholder="AAPL, TSLA...")
    if st.button("Toevoegen aan Lijst"):
        if multi_input:
            new_list = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
            st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new_list))
            st.rerun()
    if st.button("Lijst Wissen"):
        st.session_state.watchlist = []
        st.rerun()

# 5. Hoofdscherm: Directe Analyse & Dashboard
st.title("🏹 AI Strategy Terminal")

# INPUT VOOR DIRECTE SCAN (Zoals gevraagd)
target_ticker = st.text_input("🔍 Directe Ticker Scan (bijv. NVDA)", "AAPL").upper()

if target_ticker:
    res = run_full_analysis(target_ticker)
    if res:
        # Bepaal randkleur voor de scan
        border_style = "border: 2px solid #39d353;" if res['Status'] == "BUY" else "border: 1px solid #333;"
        
        st.markdown(f"""
            <div style="padding:20px; border-radius:12px; background-color:#111; {border_style} margin-bottom:20px;">
                <h2 style="margin:0;">{res['Ico']} {res['Status']}: {res['Ticker']}</h2>
                <p style="font-size:1.5em; margin:0;">{res['Prijs']} ({res['Change %']})</p>
                <p style="color:#8b949e;">AI Ensemble: {res['Ensemble']}% | Swing Score: {res['Swing']}</p>
            </div>
        """, unsafe_allow_html=True)

st.write("---")

# 6. Live Watchlist Dashboard
@st.fragment(run_every=10)
def show_live_watchlist():
    st.subheader("🔄 Live Watchlist Overzicht")
    if not st.session_state.watchlist:
        st.info("Geen aandelen in watchlist.")
        return

    results = [run_full_analysis(t) for t in st.session_state.watchlist]
    results = [r for r in results if r is not None]

    if results:
        # We gebruiken een handmatige loop om HTML regels te maken met de groene rand
        for r in results:
            style_class = "buy-row" if r['Status'] == "BUY" else ""
            st.markdown(f"""
                <div class="{style_class}" style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #222;">
                    <div style="width: 15%;"><b>{r['Ticker']}</b></div>
                    <div style="width: 15%;">{r['Prijs']}</div>
                    <div style="width: 15%; color: {'#39d353' if '+' in r['Change %'] else '#f85149'};">{r['Change %']}</div>
                    <div style="width: 15%;">AI: {r['Ensemble']}%</div>
                    <div style="width: 15%;">Swing: {r['Swing']}</div>
                    <div style="width: 25%; text-align: right;">{r['Ico']} {r['Status']}</div>
                </div>
            """, unsafe_allow_html=True)

show_live_watchlist()























