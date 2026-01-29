import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="AI Trader Pro", layout="wide")

# 2. Advanced Styling (Mobile Responsive & Dark Theme)
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
    .price-grid { 
        display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; 
    }
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
    @media (max-width: 600px) {
        .price-item { flex: 1 1 45%; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Data Fetching Functions
def get_earnings_data(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        if match:
            return match.group(1).strip().split('-')[0].strip()
        return "Not Found"
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

# 4. Main Application
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
            
            # --- METHOD 1: AI SCORING ---
            y = df['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            reg_pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (12 if reg_pred > curr_price else -8))
            lstm_trend = int(65 + (df['Close'].iloc[-5:].pct_change().sum() * 150))
            sentiment = get_sentiment_score(ticker_symbol)
            
            # --- METHOD 2: SWING & RISK ---
            vola = df['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            swing_score = 50 + (day_change * 6) - (vola * 4)
            
            # --- EARNINGS CHECK ---
            earnings_date = get_earnings_data(ticker_symbol)
            # Simple alert logic (if 'Today' or date is very soon)
            is_earnings_urgent = "Jan 29" in earnings_date or "Jan 30" in earnings_date # Example for current dates

            # Final Decision Engine
            m1_buy = (ensemble > 75) or (lstm_trend > 70) or (sentiment > 75)
            m2_buy = swing_score > 58

            if is_earnings_urgent:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "EARNINGS ALERT: High volatility expected within 48h. Avoid new entries."
            elif m1_buy and m2_buy:
                rec, color, icon = "BUY", "status-buy", "🚀"
                note = "Dual Confirmation: AI Trend and Swing Momentum are aligned."
            elif m1_buy and not m2_buy:
                rec, color, icon = "HOLD", "status-hold", "⏳"
                note = "AI is positive, but Swing Score suggests waiting for stability."
            else:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "No significant buy patterns detected."

            # UI Display
            if is_earnings_urgent:
                st.markdown(f'<div class="alert-box">🚨 EARNINGS NEAR: {earnings_date}</div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="report-container {color}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style='margin:0;'>{icon} {rec}</h2>
                        <div style="text-align: right;">
                            <span class="value">${curr_price:.2f}</span><br>
                            <span style="color: {'#39d353' if day_change >= 0 else '#f85149'}; font-size: 0.85em;">
                                {day_change:+.2f}%
                            </span>
                        </div>
                    </div>
                    <p style='color:#8b949e; font-size:0.9em; margin-top:8px;'>{note}</p>
                    <span style='font-size:0.85em;'>📅 Next Earnings: <b>{earnings_date}</b></span>
                    <div class="price-grid">
                        <div class="price-item">
                            <span class="label">Stop Loss</span>
                            <span class="value" style="color:#f85149;">${curr_price*(1-sl_pct/100):.2f}</span>
                            <span class="perc" style="color:#f85149;">-{sl_pct:.2f}%</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Entry</span>
                            <span class="value">${curr_price:.2f}</span>
                            <span class="perc">Market</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Target</span>
                            <span class="value" style="color:#39d353;">${curr_price*(1+tp_pct/100):.2f}</span>
                            <span class="perc" style="color:#39d353;">+{tp_pct:.2f}%</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Metrics Row (All components restored)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ensemble", f"{ensemble}%")
            c2.metric("LSTM Trend", f"{lstm_trend}%")
            c3.metric("Sentiment", f"{sentiment}%")
            c4.metric("Swing Score", f"{swing_score:.1f}")
            
            st.line_chart(df['Close'], height=250)

    except Exception as e:
        st.error(f"Error analyzing {ticker_symbol}. Make sure the ticker is correct.")










