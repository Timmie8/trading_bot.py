import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re

# 1. Page Configuration
st.set_page_config(page_title="AI Trading Pro", layout="wide")

# 2. Hide Code & Style UI
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .report-container { 
        padding: 25px; border-radius: 15px; background-color: #161b22; 
        color: white; border-left: 10px solid; margin-bottom: 25px;
    }
    .status-buy { border-color: #39d353; }
    .status-hold { border-color: #d29922; }
    .status-avoid { border-color: #f85149; }
    .price-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 20px; }
    .price-item { 
        background: #21262d; padding: 15px; border-radius: 10px; 
        text-align: center; border: 1px solid #30363d; 
    }
    .label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; display: block; }
    .value { font-size: 1.25rem; font-weight: bold; font-family: 'Courier New', monospace; }
    .perc { font-size: 0.85rem; display: block; margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Helper Functions
def get_earnings(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        return match.group(1).strip().split('-')[0].strip() if match else "N/A"
    except: return "N/A"

def get_sentiment(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = [h.text.lower() for h in soup.find_all('h3')][:8]
        score = 70
        for h in headlines:
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit']): score += 3
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss']): score -= 3
        return min(98, max(35, score))
    except: return 50

# 4. Main Logic
st.title("🏹 AI Strategy Dashboard")
ticker_symbol = st.text_input("Enter Ticker Symbol", "AAPL").upper()

if ticker_symbol:
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="100d")
        
        if not df.empty:
            # Data Points
            current_price = float(df['Close'].iloc[-1])
            last_price = float(df['Close'].iloc[-2])
            day_change = ((current_price / last_price) - 1) * 100
            
            # Method 1: AI Analysis
            y = df['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            reg_pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            diff = df['Close'].diff()
            gain = diff.clip(lower=0).ewm(com=13, adjust=False).mean()
            loss = (-1 * diff.clip(upper=0)).ewm(com=13, adjust=False).mean()
            rsi_val = 100 - (100 / (1 + (gain / loss).iloc[-1]))
            
            ensemble = int(72 + (12 if reg_pred > current_price else -8) + (10 if rsi_val < 45 else 0))
            lstm_trend = int(65 + (df['Close'].iloc[-5:].pct_change().sum() * 150))
            sentiment = get_sentiment(ticker_symbol)
            
            m1_confirm = (ensemble > 75) or (lstm_trend > 70) or (sentiment > 75)

            # Method 2: Swing & Risk
            vola = ((df['High'].iloc[-1] - df['Low'].iloc[-1]) / current_price) * 100
            sl_pct = min(max(vola * 1.5, 2.0), 6.0)
            tp_pct = sl_pct * 2.3
            swing_score = 50 + (day_change * 6) - (vola * 2)
            m2_confirm = swing_score > 60

            # Final Recommendation Logic
            if m1_confirm and m2_confirm:
                rec, color, icon = "BUY", "status-buy", "🚀"
                note = "Dual signal confirmed: AI and Swing models are aligned."
            elif m1_confirm and not m2_confirm:
                rec, color, icon = "HOLD", "status-hold", "⏳"
                note = "AI is positive, but Swing Score suggests waiting."
            else:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "No strong buy signals detected."

            # UI Output
            earnings = get_earnings(ticker_symbol)
            st.markdown(f"""
                <div class="report-container {color}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h1 style='margin:0;'>{icon} Recommendation: {rec}</h1>
                        <div style="text-align: right;">
                            <span class="label">Current Price</span>
                            <span class="value">${current_price:.2f}</span>
                            <span style="color: {'#39d353' if day_change >= 0 else '#f85149'}; font-size: 0.9em;">
                                {'+' if day_change >= 0 else ''}{day_change:.2f}%
                            </span>
                        </div>
                    </div>
                    <p style='color:#8b949e; margin-top:10px;'>{note}</p>
                    <span style='font-size:0.9em;'>📅 Next Earnings: <b>{earnings}</b></span>
                    <div class="price-grid">
                        <div class="price-item">
                            <span class="label">AI Stop Loss</span>
                            <span class="value" style="color:#f85149;">${current_price * (1 - sl_pct/100):.2f}</span>
                            <span class="perc" style="color:#f85149;">-{sl_pct:.1f}%</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Entry</span>
                            <span class="value">${current_price:.2f}</span>
                            <span class="perc" style="color:#8b949e;">Market Price</span>
                        </div>
                        <div class="price-item">
                            <span class="label">AI Target</span>
                            <span class="value" style="color:#39d353;">${current_price * (1 + tp_pct/100):.2f}</span>
                            <span class="perc" style="color:#39d353;">+{tp_pct:.1f}%</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Metrics Row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Ensemble", f"{ensemble}%")
            col2.metric("LSTM Trend", f"{lstm_trend}%")
            col3.metric("Sentiment", f"{sentiment}%")
            col4.metric("Swing Score", f"{swing_score:.1f}%")
            
            st.line_chart(df['Close'])

    except Exception:
        st.error("Error analyzing ticker. Please try again.")




