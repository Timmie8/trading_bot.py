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

# 2. CSS Styling - Cleaned and Simplified
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: white; }
    .report-card {
        padding: 20px; 
        border-radius: 12px; 
        background-color: #161b22; 
        color: white; 
        border: 1px solid #30363d;
        margin-bottom: 20px;
    }
    .buy-zone { border-left: 10px solid #39d353; }
    .hold-zone { border-left: 10px solid #d29922; }
    .avoid-zone { border-left: 10px solid #f85149; }
    
    .ai-reasoning {
        background-color: rgba(88, 166, 255, 0.1);
        border: 1px dashed #58a6ff;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
        color: #c9d1d9;
    }
</style>
""", unsafe_allow_html=True)

# 3. Intelligence Functions
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
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit']): score += 5
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss']): score -= 5
        return min(98, max(35, score))
    except: return 50

# 4. Main App Logic
st.title("🏹 AI Strategy Terminal")
ticker = st.text_input("Enter Ticker Symbol", "AAPL").upper()

if ticker:
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if not data.empty:
            # Calculations
            curr_p = float(data['Close'].iloc[-1])
            prev_p = float(data['Close'].iloc[-2])
            change = ((curr_p / prev_p) - 1) * 100
            
            y = data['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (12 if pred > curr_p else -8))
            sent = get_sentiment(ticker)
            vola = data['Close'].pct_change().tail(14).std() * 100
            swing = 50 + (change * 6) - (vola * 4)
            
            # Recommendation Logic
            earn = get_earnings(ticker)
            if ensemble > 75 and sent > 65:
                rec, zone, ico = "BUY", "buy-zone", "🚀"
                reason = "Strong trend detected by AI regression coupled with positive market sentiment."
            elif ensemble < 68:
                rec, zone, ico = "AVOID", "avoid-zone", "⚠️"
                reason = "Technical trend is weakening. AI suggests waiting for a better entry point."
            else:
                rec, zone, ico = "HOLD", "hold-zone", "⏳"
                reason = "Price is currently stable. No significant breakout signals identified."

            # Render HTML Card
            card_html = f"""
            <div class="report-card {zone}">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <h1 style="margin:0; color:white;">{ico} {rec}</h1>
                        <p style="color:#8b949e; margin:0;">Analysis for {ticker}</p>
                    </div>
                    <div style="text-align: right;">
                        <h2 style="margin:0; color:white;">${curr_p:.2f}</h2>
                        <p style="color:{'#39d353' if change >= 0 else '#f85149'}; margin:0; font-weight:bold;">{change:+.2f}%</p>
                    </div>
                </div>
                <div class="ai-reasoning">
                    <strong>🤖 AI REASONING:</strong><br>
                    {reason}
                </div>
                <div style="margin-top:10px; font-size:0.8rem; color:#8b949e;">
                    Next Earnings: <span style="color:white;">{earn}</span>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            # Technical Metrics
            st.subheader("Technical Intel")
            c1, c2, c3 = st.columns(3)
            c1.metric("Trend Score", f"{ensemble}%")
            c2.metric("Sentiment", f"{sent}%")
            c3.metric("Swing Score", f"{swing:.1f}")

            # Chart
            st.subheader("Price Action")
            st.line_chart(data['Close'])

    except Exception as e:
        st.error(f"Error: {e}")














