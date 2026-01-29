import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re

# 1. Page Configuration
st.set_page_config(page_title="AI Trader Pro", layout="wide")

# 2. CSS Styling (Mobile & Desktop)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .report-container { 
        padding: 18px; border-radius: 12px; background-color: #161b22; 
        color: white; border-left: 8px solid; margin-bottom: 15px;
    }
    .status-buy { border-color: #39d353; }
    .status-hold { border-color: #d29922; }
    .status-avoid { border-color: #f85149; }
    .alert-box { 
        background-color: rgba(248, 81, 73, 0.15); color: #f85149; padding: 12px; 
        border-radius: 8px; margin-bottom: 15px; border: 1px solid #f85149;
        font-weight: bold; text-align: center; font-size: 0.9em;
    }
    .price-grid { 
        display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); 
        gap: 8px; margin-top: 15px; 
    }
    .price-item { 
        background: #21262d; padding: 10px; border-radius: 8px; 
        text-align: center; border: 1px solid #30363d; 
    }
    .label { font-size: 0.65rem; color: #8b949e; text-transform: uppercase; display: block; }
    .value { font-size: 1rem; font-weight: bold; display: block; }
    .perc-sub { font-size: 0.75rem; font-weight: bold; margin-top: 2px; }
    @media (max-width: 600px) {
        .stMetric { background: #1c2128; padding: 10px; border-radius: 8px; border: 1px solid #30363d; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Backend Functions
def get_earnings(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        return match.group(1).strip().split('-')[0].strip() if match else "N/A"
    except:
        return "N/A"

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
    except:
        return 50

# 4. App Content
st.title("🏹 AI Strategy Terminal")
ticker = st.text_input("Symbol", "AAPL").upper()

if ticker:
    try:
        # Data ophalen
        stock_data = yf.Ticker(ticker)
        df = stock_data.history(period="100d")
        
        if df.empty:
            st.error("No data found for this ticker.")
        else:
            # Basis Variabelen
            curr_p = float(df['Close'].iloc[-1])
            prev_p = float(df['Close'].iloc[-2])
            change = ((curr_p / prev_p) - 1) * 100
            
            # --- AI TOOLS BEREKENING ---
            # 1. AI Ensemble (Linear Regression)
            y_vals = df['Close'].values.reshape(-1, 1)
            X_vals = np.array(range(len(y_vals))).reshape(-1, 1)
            model = LinearRegression().fit(X_vals, y_vals)
            prediction = float(model.predict(np.array([[len(y_vals)]]))[0][0])
            ensemble_score = int(72 + (12 if prediction > curr_p else -8))
            
            # 2. LSTM Trend & Sentiment
            lstm_trend = int(65 + (df['Close'].iloc[-5:].pct_change().sum() * 150))
            sentiment_score = get_sentiment(ticker)
            
            # 3. Volatility & Swing
            vola = df['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            swing_score = 50 + (change * 6) - (vola * 4)
            
            # 4. Earnings Scraper
            earn_date = get_earnings(ticker)
            is_urgent = any(d in earn_date for d in ["Jan 29", "Jan 30", "Feb 1", "Feb 2"])

            # Logica voor Advies
            if is_urgent:
                rec, col, ico, note = "AVOID", "status-avoid", "⚠️", "Earnings volatility expected."
            elif (ensemble_score > 75 or lstm_trend > 70) and swing_score > 58:
                rec, col, ico, note = "BUY", "status-buy", "🚀", "Bullish alignment detected."
            else:
                rec, col, ico, note = "HOLD", "status












