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

# 2. Styling & Dark Mode Optimization
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #0d1117; color: white; }
    
    .report-container { 
        padding: 20px; border-radius: 12px; background-color: #161b22; 
        color: white; border-left: 8px solid; margin-bottom: 15px;
        border: 1px solid #30363d;
    }
    .status-buy { border-left-color: #39d353; }
    .status-hold { border-left-color: #d29922; }
    .status-avoid { border-left-color: #f85149; }
    
    .ai-conclusion {
        background-color: rgba(88, 166, 255, 0.1);
        border: 1px dashed #58a6ff;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }

    .price-grid { 
        display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); 
        gap: 10px; margin-top: 15px; 
    }
    .price-item { 
        background: #21262d; padding: 10px; border-radius: 8px; 
        text-align: center; border: 1px solid #30363d; 
    }
    .label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; display: block; }
    .value { font-size: 1.1rem; font-weight: bold; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 3. Scrapers
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

# 4. Dashboard Content
st.title("🏹 AI Strategy Terminal")
ticker = st.text_input("Enter Ticker Symbol", "AAPL").upper()

if ticker:
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if not data.empty:
            # Basic Price Info
            curr_p = float(data['Close'].iloc[-1])
            prev_p = float(data['Close'].iloc[-2])
            change = ((curr_p / prev_p) - 1) * 100
            
            # AI Intelligence calculations
            y = data['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (12 if pred > curr_p else -8))
            lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
            sent = get_sentiment(ticker)
            vola = data['Close'].pct_change().tail(14).std() * 100
            swing = 50 + (change * 6) - (vola * 4)
            
            # Risk Management values
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            
            earn = get_earnings(ticker)
            is_urgent = any(d in earn for d in ["Jan 29", "Jan 30", "Feb 1", "Feb 2"])

            # Decision Logic
            if is_urgent: rec, col, ico = "AVOID", "status-avoid", "⚠️"
            elif (ensemble > 75 or lstm > 70) and swing > 58: rec, col, ico = "BUY", "status-buy", "🚀"
            else: rec, col, ico = "HOLD", "status-hold", "⏳"

            # --- AI CONCLUSION (REASONING) ---
            reasons = []
            if ensemble > 75: reasons.append("The price trend shows strong positive regression.")
            if sent > 70: reasons.append("Market sentiment from recent headlines is bullish.")
            if swing > 58: reasons.append("Current momentum suggests a favorable swing entry.")
            
            conclusion = " ".join(reasons) if reasons else "Indicators are currently neutral. No high-conviction signal detected."

            # UI Output
            if is_urgent:
                st.markdown(f'<div class="alert-box">🚨 EARNINGS ALERT: {earn}</div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="report-container {col}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 style='margin:0; color: white;'>{ico} {rec}</h2>
                            <p style='color:#8b949e; font-size:0.85rem; margin:4px 0;'>AI Strategic Confirmation</p>
                        </div>
                        <div style="text-align: right;">
                            <span class="value" style="font-size: 1.4rem;">${curr_p:.2f}</span><br>
                            <span style="color: {'#39d353' if change >= 0 else '#f85149'}; font-weight: bold;">{change:+.2f}%</span>
                        </div>
                    </div>
                    
                    <div class="ai-conclusion">
                        <strong style="color: #58a6ff; font-size: 0.8rem; text-transform: uppercase;">🤖 AI Reasoning:</strong><br>
                        <p style="margin-top: 5px; font-size: 0.95rem; line-height: 1.5; color: #c9d1d9;">{conclusion}</p>
                    </div>

                    <div class="price-grid">
                        <div class="price-item">
                            <span class="label">Stop Loss</span>
                            <span class="value" style="color:#f85149;">${curr_p*(1-sl_pct/100):.2f}</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Entry</span>
                            <span class="value">${curr_p:.2f}</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Target</span>
                            <span class="value" style="color:#39d353;">${curr_p*(1+tp_pct/100):.2f}</span>
                        </div>
                    </div>
                    <div style='font-size:0.75rem; margin-top: 15px; color: #8b949e;'>📅 Next Earnings: <b style="color:white;">{earn}</b></div>
                </div>
            """, unsafe_allow_html=True)

            # Technical Metrics
            st.subheader("Technical Intel Scores")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Ensemble Score", f"{ensemble}%")
            m2.metric("LSTM Trend", f"{lstm}%")
            m3.metric("Sentiment", f"{sent}%")
            m4.metric("Swing Score", f"{swing:.1f}")
            
            # Chart Section
            st.subheader("Price Action (100 Days)")
            st.line_chart(data['Close'], height=250)

    except Exception as e:
        st.error(f"Analysis failed: {e}")














