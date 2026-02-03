import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
import time

# 1. Page Configuration
st.set_page_config(page_title="AI Trader Pro", layout="wide")

# INITIALISEER WATCHLIST (Session State voor geheugen)
if 'watchlist_data' not in st.session_state:
    st.session_state.watchlist_data = pd.DataFrame(columns=["Ticker", "Prijs", "Change %", "Status"])

# 2. Styling
st.markdown("""
    <style>
    .report-container { 
        padding: 15px; border-radius: 12px; background-color: #161b22; 
        color: white; border-left: 8px solid; margin-bottom: 10px;
    }
    .status-buy { border-color: #39d353; }
    .status-hold { border-color: #d29922; }
    .status-avoid { border-color: #f85149; }
    </style>
    """, unsafe_allow_html=True)

# 3. Hulpfuncties voor Analyse
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
        headlines = [h.text.lower() for h in soup.find_all('h3')][:5]
        score = 70
        for h in headlines:
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit']): score += 3
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss']): score -= 3
        return min(98, max(35, score))
    except: return 50

def analyze_ticker(ticker_symbol):
    """Voert de volledige analyse uit voor één ticker."""
    data = yf.Ticker(ticker_symbol).history(period="100d")
    if data.empty:
        return None
    
    curr_p = float(data['Close'].iloc[-1])
    prev_p = float(data['Close'].iloc[-2])
    change = ((curr_p / prev_p) - 1) * 100
    
    # AI Logica (Linear Regression)
    y = data['Close'].values.reshape(-1, 1)
    X = np.array(range(len(y))).reshape(-1, 1)
    reg = LinearRegression().fit(X, y)
    pred = float(reg.predict(np.array([[len(y)]]))[0][0])
    
    ensemble = int(72 + (12 if pred > curr_p else -8))
    lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
    
    earn = get_earnings(ticker_symbol)
    # Simpele check voor urgentie (aanpasbaar)
    is_urgent = "Feb" in earn or "Jan" in earn 

    if is_urgent: rec, col, ico = "AVOID", "status-avoid", "⚠️"
    elif (ensemble > 75 or lstm > 70): rec, col, ico = "BUY", "status-buy", "🚀"
    else: rec, col, ico = "HOLD", "status-hold", "⏳"
    
    return {
        "Ticker": ticker_symbol,
        "Prijs": round(curr_p, 2),
        "Change %": round(change, 2),
        "Status": f"{ico} {rec}",
        "Color": col,
        "Data": data
    }

# 4. Sidebar Watchlist
with st.sidebar:
    st.header("📋 Live Watchlist")
    
    # Input voor meerdere tickers
    new_tickers = st.text_input("Voeg tickers toe (scheid met komma)", "AAPL, TSLA, NVDA")
    
    if st.button("Update/Start Watchlist"):
        ticker_list = [t.strip().upper() for t in new_tickers.split(",")]
        results = []
        for t in ticker_list:
            res = analyze_ticker(t)
            if res:
                results.append({
                    "Ticker": res["Ticker"],
                    "Prijs": res["Prijs"],
                    "Change %": res["Change %"],
                    "Status": res["Status"]
                })
        st.session_state.watchlist_data = pd.DataFrame(results)

    # Toon de watchlist
    if not st.session_state.watchlist_data.empty:
        st.dataframe(st.session_state.watchlist_data, hide_index=True)
        
        if st.button("Lijst wissen"):
            st.session_state.watchlist_data = pd.DataFrame(columns=["Ticker", "Prijs", "Change %", "Status"])
            st.rerun()

# 5. Dashboard Content
st.title("🏹 AI Strategy Terminal")

# Als er tickers in de lijst staan, toon ze op het hoofdscherm
if not st.session_state.watchlist_data.empty:
    for _, row in st.session_state.watchlist_data.iterrows():
        # Haal verse data op voor het hoofdscherm
        analysis = analyze_ticker(row['Ticker'])
        
        if analysis:
            with st.expander(f"Details voor {analysis['Ticker']} - {analysis['Status']}", expanded=True):
                st.markdown(f"""
                    <div class="report-container {analysis['Color']}">
                        <div style="display: flex; justify-content: space-between;">
                            <h3>{analysis['Ticker']} - ${analysis['Prijs']}</h3>
                            <h3 style="color:{'#39d353' if analysis['Change %'] >= 0 else '#f85149'}">{analysis['Change %']}%</h3>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.line_chart(analysis['Data']['Close'], height=150)
else:
    st.info("Voer tickers in de sidebar in om de analyse te starten.")

# Automatische verversing (elke 60 seconden)
# Dit is een simpele manier om Streamlit te triggeren
time.sleep(1) # Voorkomt CPU overbelasting
if st.checkbox("Live Updates inschakelen (elke 60s)"):
    time.sleep(60)
    st.rerun()



















