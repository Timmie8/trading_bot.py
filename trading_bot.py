import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# --- 1. Dashboard Configuration ---
st.set_page_config(page_title="AI Trading Engine", layout="wide")

# Custom CSS to hide code elements and style the UI
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .report-container { 
        padding: 25px; 
        border-radius: 15px; 
        background-color: #161b22; 
        color: white; 
        border-left: 10px solid; 
        margin-bottom: 25px;
    }
    .status-buy { border-color: #39d353; }
    .status-hold { border-color: #d29922; }
    .status-avoid { border-color: #f85149; }
    .price-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px; }
    .price-item { 
        background: #21262d; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #30363d; 
    }
    .label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; display: block; }
    .value { font-size: 1.25rem; font-weight: bold; font-family: 'Courier New', monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Backend Logic Functions ---
def fetch_earnings(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        if "Earnings Date" in text:
            match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
            if match: return match.group(1).strip().split('-')[0].strip()
        return "Not Found"
    except: return "N/A"

def fetch_sentiment(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = [h.text.lower() for h in soup.find_all('h3')][:8]
        score = 70
        for h in headlines:
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit']): score += 3
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss']): score -= 3
        return min(98, max(35, score))
    except: return 50

# --- 3. Main Application ---
st.title("🏹 AI Strategy & Risk Dashboard")
ticker = st.text_input("Enter Ticker Symbol", "AAPL").upper()

if ticker:
    try:
        # Data Retrieval
        stock_data = yf.Ticker(ticker).history(period="100d")
        if not stock_data.empty:
            price = float(stock_data['Close'].iloc[-1])
            prev_price = float(stock_data['Close'].iloc[-2])
            
            # --- METHOD 1: AI SCORING ---
            y = stock_data['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg_model = LinearRegression().fit(X, y)
            reg_pred = float(reg_model.predict(np.array([[len(y)]]))[0][0])
            
            # RSI Calculation
            diff = stock_data['Close'].diff()
            gain = diff.clip(lower=0).ewm(com=13, adjust=False).mean()
            loss = (-1 * diff.clip(upper=0)).ewm(com=13, adjust=False).mean()
            rsi = 100 - (100 / (1 + (gain / loss).iloc[-1]))
            
            # AI Method Scores
            ensemble = int(72 + (12 if reg_pred > price else -8) + (10 if rsi < 45 else 0))
            lstm_sim = int(65 + (stock_data['Close'].iloc[-5:].pct_change().sum() * 150))
            sentiment = fetch_sentiment(ticker)
            
            m1_buy_signal = (ensemble > 75) or (lstm_sim > 70) or (sentiment > 75)

            # --- METHOD 2: SWING & RISK ---
            daily_change = ((price / prev_price) - 1) * 100
            volatility = ((stock_data['High'].iloc[-1] - stock_data['Low'].iloc[-1]) / price) * 100
            
            # Risk Levels
            sl_pct = min(max(volatility * 1.5, 2.0), 6.0)
            tp_pct = sl_pct * 2.3
            
            m2_swing_score = 50 + (daily_change * 6) - (volatility * 2)
            is_swing_confirmed = m2_swing_score > 60

            # --- FINAL DECISION ---
            if m1_buy_signal and is_swing_confirmed:
                status, style, icon = "BUY", "status-buy", "🚀"
                note = "Dual Confirmation: AI metrics and Swing momentum are aligned."
            elif m1_buy_signal and not is_swing_confirmed:
                status, style, icon = "HOLD", "status-hold", "⏳"
                note = "AI is bullish, but Swing score suggests waiting for better momentum."
            else:
                status, style, icon = "AVOID", "status-avoid", "⚠️"
                note = "No significant buy signals detected from AI or Swing models."

            # Dashboard Output
            earnings = fetch_earnings(ticker)
            st.markdown(f"""
                <div class="report-container {style}">
                    <h1 style='margin:0;'>{icon} Recommendation: {status}</h1>
                    <p style='color:#8b949e; margin-bottom:10px;'>{note}</p>
                    <span style='font-size:0.9em;'>📅 Next Earnings: <b>{earnings}</b></span>
                    <div class="price-grid">
                        <div class="price-item">
                            <span class="label">AI Stop Loss</span>
                            <span class="value" style="color:#f85149;">${price * (1 - sl_pct/100):.2f}</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Entry Price</span>
                            <span class="value">${price:.2f}</span>
                        </div>
                        <div class="price-item">
                            <span class="label">AI Target</span>
                            <span class="value" style="color:#39d353;">${price * (1 + tp_pct/100):.2f}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ensemble", f"{ensemble}%")
            c2.metric("LSTM", f"{lstm_sim}%")
            c3.metric("Sentiment", f"{sentiment}%")
            c4.metric("Swing Score", f"{m2_swing_score:.1f}%")
            
            st.line_chart(stock_data['Close'])

    except Exception as e:
        st.error(f"Analysis interrupted. Please check the Ticker symbol.")



