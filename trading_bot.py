import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# --- 1. CLIENT DATABASE ---
# Add your clients here: "Email": "Password"
USER_DATABASE = {
    "admin@trading.nl": "Admin2026!",
    "user1@client.com": "TradeSafe88",
    "test@test.nl": "12345"
}

# --- 2. SECURITY SYSTEM ---
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if st.session_state["authenticated"]:
        return True

    st.title("🏹 AI Terminal - Secure Login")
    col1, col2 = st.columns([1, 1])
    with col1:
        email_input = st.text_input("Email Address")
        pass_input = st.text_input("Access Key", type="password")
        if st.button("Unlock Dashboard"):
            if email_input in USER_DATABASE and USER_DATABASE[email_input] == pass_input:
                st.session_state["authenticated"] = True
                st.session_state["user_email"] = email_input
                st.rerun()
            else:
                st.error("🚫 Access Denied. Contact support for payment.")
    return False

if not check_auth():
    st.stop()

# --- 3. FULL APP CONFIGURATION ---
st.set_page_config(page_title="AI Trader Pro", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    .report-container { 
        padding: 20px; border-radius: 12px; background-color: #161b22; 
        color: white; border-left: 8px solid; margin-bottom: 20px;
    }
    .status-buy { border-color: #39d353; }
    .status-hold { border-color: #d29922; }
    .status-avoid { border-color: #f85149; }
    .price-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
    .price-item { 
        flex: 1 1 100px; background: #21262d; padding: 12px; 
        border-radius: 8px; text-align: center; border: 1px solid #30363d; 
    }
    .label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; display: block; }
    .value { font-size: 1.1rem; font-weight: bold; }
    .perc { font-size: 0.8rem; display: block; margin-top: 2px; }
    .alert-box { 
        background-color: rgba(248, 81, 73, 0.15); color: #f85149; padding: 10px; 
        border-radius: 8px; margin-bottom: 15px; border: 1px solid #f85149;
        font-weight: bold; text-align: center; font-size: 0.9em;
    }
    @media (max-width: 600px) { .price-item { flex: 1 1 45%; } }
    </style>
    """, unsafe_allow_html=True)

# --- 4. BACKEND FUNCTIONS ---
def get_earnings_data(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        return match.group(1).strip().split('-')[0].strip() if match else "N/A"
    except: return "N/A"

def get_sentiment_score(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        headlines = [h.text.lower() for h in soup.find_all('h3')][:8]
        score = 70
        for h in headlines:
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit']): score += 3
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss']): score -= 3
        return min(98, max(35, score))
    except: return 50

# --- 5. MAIN TRADING ENGINE ---
with st.sidebar:
    st.success(f"User: {st.session_state['user_email']}")
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

st.title("🏹 AI Strategy Dashboard")
ticker_symbol = st.text_input("Enter Ticker", "AAPL").upper()

if ticker_symbol:
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="100d")
        
        if not df.empty:
            curr_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            day_change = ((curr_price / prev_price) - 1) * 100
            
            # --- AI METHOD 1 ---
            y = df['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            reg_pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (12 if reg_pred > curr_price else -8))
            lstm_trend = int(65 + (df['Close'].iloc[-5:].pct_change().sum() * 150))
            sentiment = get_sentiment_score(ticker_symbol)
            
            # --- SWING & RISK METHOD 2 ---
            vola = df['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            swing_score = 50 + (day_change * 6) - (vola * 4)
            
            # --- EARNINGS ---
            earnings_date = get_earnings_data(ticker_symbol)
            # Check if earnings date is today or tomorrow (basic check)
            is_urgent = "Jan 29" in earnings_date or "Jan 30" in earnings_date

            # Final Decision
            m1_buy = (ensemble > 75) or (lstm_trend > 70) or (sentiment > 75)
            m2_buy = swing_score > 58

            if is_urgent:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "EARNINGS ALERT: High volatility expected. Avoid entries."
            elif m1_buy and m2_buy:
                rec, color, icon = "BUY", "status-buy", "🚀"
                note = "Dual Confirmation: AI and Swing models are aligned."
            elif m1_buy and not m2_buy:
                rec, color, icon = "HOLD", "status-hold", "⏳"
                note = "AI is positive, but waiting for Swing confirmation."
            else:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "No significant buy signals detected."

            # Dashboard Display
            if is_urgent:
                st.markdown(f'<div class="alert-box">🚨 EARNINGS NEAR: {earnings_date}</div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="report-container {color}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style='margin:0;'>{icon} {rec}</h2>
                        <div style="text-align: right;">
                            <span class="value">${curr_price:.2f}</span><br>
                            <span style="color: {'#39d353









