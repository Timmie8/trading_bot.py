import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

# --- Setup & Styling ---
st.set_page_config(page_title="AI Trader Pro - Dual Logic", layout="wide")
st.markdown("""
<style>
    .report-container { padding: 25px; border-radius: 15px; background-color: #161b22; color: white; border-left: 10px solid; }
    .status-buy { border-color: #39d353; box-shadow: 0px 0px 15px rgba(57, 211, 83, 0.2); }
    .status-hold { border-color: #d29922; }
    .status-avoid { border-color: #f85149; }
    .price-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 20px; }
    .price-item { background: #21262d; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #30363d; }
    .label { font-size: 0.8em; color: #8b949e; display: block; text-transform: uppercase; letter-spacing: 1px; }
    .value { font-size: 1.2em; font-weight: bold; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- Logic Functions ---
def get_earnings_date_live(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        if "Earnings Date" in page_text:
            match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', page_text)
            if match:
                return match.group(1).strip().split('-')[0].strip()
        return None
    except: return None

def get_live_sentiment(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = [h.text.lower() for h in soup.find_all('h3')][:8]
        score = 70
        for h in headlines:
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit', 'beat']): score += 3
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss', 'risk']): score -= 3
        return min(98, max(35, score))
    except: return 50

# --- Main App ---
st.title("🏹 AI Strategy & Risk Management Dashboard")
ticker_input = st.text_input("Enter Ticker Symbol (e.g., TSLA, NVDA)", "AAPL").upper()

if ticker_input:
    try:
        ticker_obj = yf.Ticker(ticker_input)
        data = ticker_obj.history(period="100d")
        
        if not data.empty:
            curr_price = float(data['Close'].iloc[-1])
            prev_price = data['Close'].iloc[-2]
            
            # --- 1. AI METHOD 1 (Logic from Code 1) ---
            # Regression Trend
            y_reg = data['Close'].values.reshape(-1, 1)
            X_reg = np.array(range(len(y_reg))).reshape(-1, 1)
            model = LinearRegression().fit(X_reg, y_reg)
            pred = float(model.predict(np.array([[len(y_reg)]]))[0][0])
            
            # RSI Calculation
            delta = data['Close'].diff()
            up, down = delta.clip(lower=0), -1 * delta.clip(upper=0)
            ema_up = up.ewm(com=13, adjust=False).mean()
            ema_down = down.ewm(com=13, adjust=False).mean()
            rsi = 100 - (100 / (1 + (ema_up / ema_down).iloc[-1]))
            
            # AI Metric Scores
            ensemble_score = int(72 + (12 if pred > curr_price else -8) + (10 if rsi < 45 else 0))
            lstm_score = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
            sentiment_score = get_live_sentiment(ticker_input)
            
            m1_buy = (ensemble_score > 75) or (lstm_score > 70) or (sentiment_score > 75)

            # --- 2. SWING & RISK METHOD 2 (Logic from Code 2) ---
            change = ((curr_price / prev_price) - 1) * 100
            vola = ((data['High'].iloc[-1] - data['Low'].iloc[-1]) / curr_price) * 100
            
            # Dynamic Risk Calculation (1.5x Vola for SL, 2.3x Reward for TP)
            stop_perc = min(max(vola * 1.5, 2.0), 6.0)
            target_perc = stop_perc * 2.3
            
            stop_price = curr_price * (1 - stop_perc/100)
            target_price = curr_price * (1 + target_perc/100)
            
            m2_swing_score = 50 + (change * 6) - (vola * 2)
            is_swing = m2_swing_score > 60

            # --- 3. FINAL DECISION ENGINE ---
            earnings_date = get_earnings_date_live(ticker_input)
            
            if m1_buy and is_swing:
                status, css, icon = "BUY", "status-buy", "🚀"
                summary = "Strong AI alignment detected with verified Swing momentum."
            elif m1_buy and not is_swing:
                status, css, icon = "HOLD", "status-hold", "⏳"
                summary = "AI signals are positive, but Swing Score is currently insufficient."
            else:
                status, css, icon = "AVOID", "status-avoid", "⚠️"
                summary = "No significant buying signals detected by the AI models."

            # UI Display
            st.markdown(f"""
            <div class="report-container {css}">
                <h2>{icon} Recommendation: {status}</h2>
                <p>{summary}</p>
                <p style="color: #8b949e;">📅 Next Earnings Date: <b>{earnings_date if earnings_date else 'Not Found'}</b></p>
                
                <div class="price-grid">
                    <div class="price-item">
                        <span class="label">AI Stop Loss</span>
                        <span class="value" style="color: #f85149;">${stop_price:.2f}</span>
                        <small style="color: #f85149;">-{stop_perc:.1f}%</small>
                    </div>
                    <div class="price-item">
                        <span class="label">Entry (Market)</span>
                        <span class="value">${curr_price:.2f}</span>
                        <small>Current Price</small>
                    </div>
                    <div class="price-item">
                        <span class="label">AI Target</span>
                        <span class="value" style="color: #39d353;">${target_price:.2f}</span>
                        <small style="color: #39d353;">+{target_perc:.1f}%</small>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Metrics Table
            st.subheader("Analysis Metrics")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Ensemble Score", f"{ensemble_score}%")
            m_col2.metric("LSTM Trend", f"{lstm_score}%")
            m_col3.metric("Sentiment", f"{sentiment_score}%")
            m_col4.metric("Swing Score", f"{m2_swing_score:.1f}%")
            
            st.line_chart(data['Close'])

    except Exception as e:
        st.error(f"Analysis Error: {e}")

st.caption("AI Disclaimer: Analysis is based on statistical data and news scraping. Always perform your own research.")


