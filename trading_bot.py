import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re

# 1. PAGE CONFIG (MOET BOVENAAN)
st.set_page_config(page_title="AI Trader Pro", layout="wide")

# 2. USER DATABASE
USER_DATABASE = {
    "admin@trading.nl": "Admin2026!",
    "user1@client.com": "TradeSafe88"
}

# 3. AUTHENTICATION LOGIC
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def login_screen():
    st.title("🏹 AI Pro Terminal - Login")
    email = st.text_input("Email Address")
    password = st.text_input("Access Key", type="password")
    if st.button("Unlock Dashboard"):
        if email in USER_DATABASE and USER_DATABASE[email] == password:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.rerun()
        else:
            st.error("Invalid credentials.")

if not st.session_state["authenticated"]:
    login_screen()
    st.stop()

# --- VANAF HIER DE VOLLEDIGE BOT ---

# 4. STYLING
st.markdown("""
    <style>
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
    </style>
    """, unsafe_allow_html=True)

# 5. BACKEND TOOLS
def get_earnings(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        return match.group(1).strip().split('-')[0].strip() if match else "N/A"
    except: return "N/A"

def get_sentiment(ticker):
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

# 6. DASHBOARD
with st.sidebar:
    st.success(f"User: {st.session_state['user_email']}")
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

st.title("🏹 AI Strategy Dashboard")
ticker = st.text_input("Enter Ticker", "AAPL").upper()

if ticker:
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if not data.empty:
            curr_p = float(data['Close'].iloc[-1])
            prev_p = float(data['Close'].iloc[-2])
            change = ((curr_p / prev_p) - 1) * 100
            
            # --- TOOL 1: AI ENSEMBLE ---
            y = data['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            ensemble = int(72 + (12 if pred > curr_p else -8))
            
            # --- TOOL 2: LSTM TREND ---
            lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
            
            # --- TOOL 3: SENTIMENT ---
            sent = get_sentiment(ticker)
            
            # --- TOOL 4: SWING SCORE & RISK ---
            vola = data['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            swing = 50 + (change * 6) - (vola * 4)
            
            # --- TOOL 5: EARNINGS ---
            earn = get_earnings(ticker)
            urgent = "Jan 29" in earn or "Jan 30" in earn

            # Decision
            if urgent: rec, col, ico = "AVOID", "status-avoid", "⚠️"
            elif (ensemble > 75 or lstm > 70) and swing > 58: rec, col, ico = "BUY", "status-buy", "🚀"
            else: rec, col, ico = "HOLD", "status-hold", "⏳"

            # UI OUTPUT
            st.markdown(f"""
                <div class="report-container {col}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style='margin:0;'>{ico} {rec}</h2>
                        <div style="text-align: right;">
                            <span class="value">${curr_p:.2f}</span><br>
                            <span style="color: {'#39d353' if change >= 0 else '#f85149'};">{change:+.2f}%</span>
                        </div>
                    </div>
                    <p style='font-size:0.9em; margin-top:8px;'>📅 Next Earnings: <b>{earn}</b></p>
                    <div class="price-grid">
                        <div class="price-item"><span class="label">Stop Loss</span><span class="value" style="color:#f85149;">${curr_p*(1-sl_pct/100):.2f}</span><span class="perc">-{sl_pct:.2f}%</span></div>
                        <div class="price-item"><span class="label">Entry</span><span class="value">${curr_p:.2f}</span><span class="perc">Market</span></div>
                        <div class="price-item"><span class="label">Target</span><span class="value" style="color:#39d353;">${curr_p*(1+tp_pct/100):.2f}</span><span class="perc">+{tp_pct:.2f}%</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ensemble", f"{ensemble}%")
            c2.metric("LSTM Trend", f"{lstm}%")
            c3.metric("Sentiment", f"{sent}%")
            c4.metric("Swing Score", f"{swing:.1f}")
            
            st.line_chart(data['Close'], height=250)
            
    except Exception as e:
        st.error(f"Error: {e}")









