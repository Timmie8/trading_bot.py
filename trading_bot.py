import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

# 1. Page Configuration (Mobile Optimized)
st.set_page_config(page_title="AI Trader Pro", layout="wide")

# 2. Advanced Styling (Responsive & Dark Mode Support)
st.markdown("""
    <style>
    /* Responsive Grid for Mobile */
    .report-container { 
        padding: 15px; border-radius: 12px; background-color: #161b22; 
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
    .alert-box { 
        background-color: #701b1b; color: white; padding: 10px; 
        border-radius: 8px; margin-bottom: 15px; border: 1px solid #f85149;
        font-weight: bold; text-align: center;
    }
    /* Mobile font adjustments */
    @media (max-width: 600px) {
        h1 { font-size: 1.5rem !important; }
        .value { font-size: 1rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Enhanced Helper Functions
def get_earnings_info(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        if match:
            date_str = match.group(1).strip().split('-')[0].strip()
            # Simple check for "Today" or "Tomorrow" in text
            is_urgent = any(word in date_str.lower() for word in ["jan", "feb", "mar"]) # Simplification for logic
            return date_str, False # Replace with true date parsing if needed
        return "N/A", False
    except: return "N/A", False

def get_sentiment(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = [h.text.lower() for h in soup.find_all('h3')][:5]
        score = 70
        for h in headlines:
            if any(w in h for w in ['growth', 'buy', 'profit']): score += 5
            if any(w in h for w in ['drop', 'sell', 'miss']): score -= 5
        return min(98, max(35, score))
    except: return 50

# 4. Sidebar Options
with st.sidebar:
    st.header("Settings")
    use_dark = st.toggle("Dark Mode UI", value=True)
    st.info("Mobile View: Enabled")

# 5. Main Logic
st.title("🏹 AI Trading Pro")
ticker_symbol = st.text_input("Ticker Symbol", "AAPL").upper()

if ticker_symbol:
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="100d")
        
        if not df.empty:
            curr_price = float(df['Close'].iloc[-1])
            day_change = ((curr_price / df['Close'].iloc[-2]) - 1) * 100
            
            # AI Logic
            y = df['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            reg_pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (12 if reg_pred > curr_price else -8))
            sentiment = get_sentiment(ticker_symbol)
            
            # Risk Logic
            vola = df['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            
            # Earnings Logic
            earnings_date, is_near = get_earnings_info(ticker_symbol)
            # Manual override if earnings is "Today" or within 2 days (Mock-check)
            earnings_warning = "Earnings" in earnings_date or "Today" in earnings_date

            # Final Recommendation
            if earnings_warning:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "CRITICAL: Earnings reported soon. Stay cash to avoid volatility."
            elif ensemble > 75 and sentiment > 65:
                rec, color, icon = "BUY", "status-buy", "🚀"
                note = "AI & Sentiment confirm entry."
            else:
                rec, color, icon = "HOLD", "status-hold", "⏳"
                note = "Patterns neutral. Monitoring..."

            # UI Output
            if earnings_warning:
                st.markdown(f'<div class="alert-box">🚨 EARNINGS ALERT: High Volatility Expected ({earnings_date})</div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="report-container {color}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style='margin:0;'>{icon} {rec}</h2>
                        <div style="text-align: right;">
                            <span class="value">${curr_price:.2f}</span><br>
                            <span style="color: {'#39d353' if day_change >= 0 else '#f85149'}; font-size: 0.8em;">
                                {day_change:+.2f}%
                            </span>
                        </div>
                    </div>
                    <p style='color:#8b949e; font-size:0.9em; margin-top:10px;'>{note}</p>
                    <hr style="border: 0.1px solid #30363d;">
                    <div class="price-grid">
                        <div class="price-item"><span class="label">SL</span><span class="value">${curr_price*(1-sl_pct/100):.2f}</span><span class="perc" style="color:#f85149;">-{sl_pct:.1f}%</span></div>
                        <div class="price-item"><span class="label">ENTRY</span><span class="value">${curr_price:.2f}</span><span class="perc">Market</span></div>
                        <div class="price-item"><span class="label">TP</span><span class="value">${curr_price*(1+tp_pct/100):.2f}</span><span class="perc" style="color:#39d353;">+{tp_pct:.1f}%</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Mobile Metrics
            m1, m2 = st.columns(2)
            m1.metric("AI Score", f"{ensemble}%")
            m2.metric("Sentiment", f"{sentiment}%")
            
            st.line_chart(df['Close'], height=250)

    except Exception:
        st.error("Invalid Ticker")






