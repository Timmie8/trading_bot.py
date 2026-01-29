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

# 2. CSS Styling
# We force the theme to be dark and define our custom boxes
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: white; }
    .report-card { 
        padding: 20px; border-radius: 12px; background-color: #161b22; 
        border: 1px solid #30363d; margin-bottom: 20px;
    }
    .buy-border { border-left: 10px solid #39d353; }
    .hold-border { border-left: 10px solid #d29922; }
    .avoid-border { border-left: 10px solid #f85149; }
    
    .ai-box {
        background-color: rgba(88, 166, 255, 0.1);
        border: 1px dashed #58a6ff;
        padding: 15px;
        border-radius: 8px;
        margin: 15px 0;
    }
    .price-item { 
        background: #21262d; padding: 10px; border-radius: 8px; 
        text-align: center; border: 1px solid #30363d; 
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Helper Functions
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

# 4. Main Application
st.title("🏹 AI Strategy Terminal")
ticker_input = st.text_input("Enter Ticker Symbol", "AAPL").upper()

if ticker_input:
    try:
        # Fetch Data
        df = yf.download(ticker_input, period="100d", interval="1d")
        
        if not df.empty:
            # Data Cleanup for Charts
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Basic Price Info
            curr_p = float(df['Close'].iloc[-1])
            prev_p = float(df['Close'].iloc[-2])
            change_pct = ((curr_p / prev_p) - 1) * 100
            
            # AI Calculations
            y = df['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (15 if pred > curr_p else -10))
            sent_score = get_sentiment(ticker_input)
            vola = df['Close'].pct_change().tail(14).std() * 100
            
            # Risk Management
            sl_val = curr_p * 0.95  # Standard 5% Stop Loss
            tp_val = curr_p * 1.12  # Standard 12% Take Profit
            
            # Decision Logic
            earn_date = get_earnings(ticker_input)
            if ensemble > 75 and sent_score > 65:
                rec, border_class, icon = "BUY", "buy-border", "🚀"
                reasoning = "AI analysis confirms a strong bullish trend combined with positive market sentiment."
            elif ensemble < 65:
                rec, border_class, icon = "AVOID", "avoid-border", "⚠️"
                reasoning = "Technical indicators suggest a downward trend. High risk of further decline."
            else:
                rec, border_class, icon = "HOLD", "hold-border", "⏳"
                reasoning = "Price is currently consolidating. No clear breakout signal detected."

            # --- RENDER UI ---
            # 1. The Main Report Card
            st.markdown(f"""
                <div class="report-card {border_class}">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <h1 style="margin:0;">{icon} {rec}</h1>
                            <p style="color:#8b949e;">AI Strategy Analysis for {ticker_input}</p>
                        </div>
                        <div style="text-align: right;">
                            <h2 style="margin:0;">${curr_p:.2f}</h2>
                            <p style="color: {'#39d353' if change_pct >= 0 else '#f85149'}; font-weight: bold;">{change_pct:+.2f}%</p>
                        </div>
                    </div>
                    
                    <div class="ai-box">
                        <b style="color: #58a6ff;">🤖 AI REASONING:</b><br>
                        <p style="margin-top:5px;">{reasoning}</p>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <div class="price-item" style="flex:1;">
                            <small style="color:#8b949e;">STOP LOSS</small><br>
                            <b style="color:#f85149;">${sl_val:.2f}</b>
                        </div>
                        <div class="price-item" style="flex:1;">
                            <small style="color:#8b949e;">ENTRY</small><br>
                            <b>${curr_p:.2f}</b>
                        </div>
                        <div class="price-item" style="flex:1;">
                            <small style="color:#8b949e;">TARGET</small><br>
                            <b style="color:#39d353;">${tp_val:.2f}</b>
                        </div>
                    </div>
                    <p style="font-size: 0.8rem; margin-top:10px; color:#8b949e;">Earnings Date: {earn_date}</p>
                </div>
            """, unsafe_allow_html=True)

            # 2. Metrics Section
            col1, col2, col3 = st.columns(3)
            col1.metric("Trend Score", f"{ensemble}%")
            col2.metric("Sentiment", f"{sent_score}%")
            col3.metric("Volatility", f"{vola:.2f}%")

            # 3. Chart Section
            st.subheader("Price History (100 Days)")
            st.line_chart(df['Close'])

    except Exception as e:
        st.error(f"Analysis failed: {e}")













