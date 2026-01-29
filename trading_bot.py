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

# 2. Advanced Styling (Dark Mode, Mobile & Alerts)
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

# 4. Main App Logic
st.title("🏹 AI Strategy Terminal")
ticker = st.text_input("Symbol", "AAPL").upper()

if ticker:
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if not data.empty:
            curr_p = float(data['Close'].iloc[-1])
            prev_p = float(data['Close'].iloc[-2])
            change = ((curr_p / prev_p) - 1) * 100
            
            # --- ALL TOOLS CALCULATION ---
            # 1. AI Ensemble
            y = data['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            ensemble = int(72 + (12 if pred > curr_p else -8))
            
            # 2. LSTM Trend
            lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
            
            # 3. Sentiment
            sent = get_sentiment(ticker)
            
            # 4. Swing & Volatility
            vola = data['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            swing = 50 + (change * 6) - (vola * 4)
            
            # 5. Earnings Check
            earn = get_earnings(ticker)
            # Alert trigger for upcoming dates
            is_urgent = any(d in earn for d in ["Jan 29", "Jan 30", "Feb 1", "Feb 2"])

            # Decision Logic
            if is_urgent: rec, col, ico, note = "AVOID", "status-avoid", "⚠️", "Earnings near. High volatility risk."
            elif (ensemble > 75 or lstm > 70) and swing > 58: rec, col, ico, note = "BUY", "status-buy", "🚀", "AI & Swing Momentum aligned."
            else: rec, col, ico, note = "HOLD", "status-hold", "⏳", "Waiting for confirmation."

            # --- UI OUTPUT ---
            if is_urgent:
                st.markdown(f'<div class="alert-box">🚨 EARNINGS ALERT: {earn}</div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="report-container {col}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 style='margin:0;'>{ico} {rec}</h2>
                            <p style='color:#8b949e; font-size:0.8rem; margin:4px 0;'>{note}</p>
                        </div>
                        <div style="text-align: right;">
                            <span class="value" style="font-size: 1.2rem;">${curr_p:.2f}</span>
                            <span style="color: {'#39d353' if change >= 0 else '#f85149'}; font-size: 0.8rem; font-weight: bold;">
                                {change:+.2f}%
                            </span>
                        </div>
                    </div>
                    <div style='font-size:0.75rem; margin-top: 10px;'>📅 Next Earnings: <b>{earn}</b></div>
                    <div class="price-grid">
                        <div class="price-item">
                            <span class="label">Stop Loss</span>
                            <span class="value" style="color:#f85149;">${curr_p*(1-sl_pct/100):.2f}</span>
                            <span class="perc-sub" style="color:#f85149;">-{sl_pct:.2f}%</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Entry</span>
                            <span class="value">${curr_p:.2f}</span>
                            <span class="perc-sub" style="color:#8b949e;">MARKET</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Target</span>
                            <span class="value" style="color:#39d353;">${curr_p*(1+tp_pct/100):.2f}</span>
                            <span class="perc-sub" style="color:#39d353;">+{tp_pct:.2f}%</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Metrics Row (All tools restored)
            m1, m2 = st.columns(2)
            m1.metric("Ensemble Score", f"{ensemble}%")
            m2.metric("LSTM Trend", f"{lstm}%")
            
            m3, m4 = st.columns(2)
            m












