import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
import time

# 1. Pagina Configuratie & Forceren Zwart Thema
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
        width: 100%;
    }
    .stButton>button:hover { border-color: #39d353 !important; color: #39d353 !important; }
    
    /* Tabel styling */
    .stTable { background-color: #000000 !important; border: 1px solid #333 !important; }
    th { color: #39d353 !important; }
    
    /* Input velden */
    input { background-color: #111 !important; color: white !important; border: 1px solid #444 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Watchlist Geheugen (Altijd als lijst voor Live Update)
if 'watchlist' not in st.session_state or not isinstance(st.session_state.watchlist, list):
    st.session_state.watchlist = ["AAPL", "NVDA"]

# 3. Originele Scrapers & AI Logica
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
    """De exacte AI berekeningen uit jouw basiscode."""
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if data.empty: return None
        
        curr_p = float(data['Close'].iloc[-1])
        prev_p = float(data['Close'].iloc[-2])
        change = ((curr_p / prev_p) - 1) * 100
        
        # AI & Regression
        y = data['Close'].values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        
        # Exacte Score Formules
        ensemble = int(72 + (12 if pred > curr_p else -8))
        lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
        sent = get_sentiment(ticker)
        vola = data['Close'].pct_change().tail(14).std() * 100
        swing = 50 + (change * 6) - (vola * 4)
        
        earn = get_earnings(ticker)
        is_urgent = any(d in earn for d in ["Jan 29", "Jan 30", "Feb 1", "Feb 2", "Feb 3", "Feb 4"])

        # Decision Logic
        if is_urgent: rec, ico = "AVOID", "⚠️"
        elif (ensemble > 75 or lstm > 70) and swing > 58: rec, ico = "BUY", "🚀"
        else: rec, ico = "HOLD", "⏳"
        
        return {
            "Ticker": ticker,
            "Prijs": f"${curr_p:.2f}",
            "Change %": f"{change:+.2f}%",
            "Ensemble": f"{ensemble}%",
            "LSTM": f"{lstm}%",
            "Swing": round(swing, 1),
            "Status": f"{ico} {rec}",
            "Earnings": earn
        }
    except: return None

# 4. Sidebar: Multi-ticker Input
with st.sidebar:
    st.header("📋 Beheer Watchlist")
    multi_input = st.text_input("Tickers (komma-gescheiden)", placeholder="AAPL, TSLA, NVDA")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Toevoegen"):
            if multi_input:
                new_list = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
                st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new_list))
                st.rerun()
    with c2:
        if st.button("Reset"):
            st.session_state.watchlist = []
            st.rerun()

# 5. Dashboard (Live fragment voor 10s updates)
st.title("🏹 AI Strategy Terminal")

@st.fragment(run_every=10)
def show_live_dashboard():
    if not st.session_state.watchlist:
        st.info("Voeg tickers toe in de sidebar.")
        return

    st.write(f"⏱️ **Live AI Analyse Update:** {time.strftime('%H:%M:%S')}")
    
    results = []
    for t in st.session_state.watchlist:
        res = run_full_analysis(t)
        if res:
            results.append(res)
    
    if results:
        df = pd.DataFrame(results)
        # Tabel met EXACT dezelfde scores als gevraagd
        st.table(df[['Ticker', 'Prijs', 'Change %', 'Ensemble', 'LSTM', 'Swing', 'Status', 'Earnings']])
        
        # Focus kaart voor de eerste ticker
        st.write("---")
        st.subheader("🔍 Laatste Analyse")
        top = results[0]
        st.metric(f"{top['Ticker']} AI Score", top['Ensemble'], top['Change %'])

show_live_dashboard()























