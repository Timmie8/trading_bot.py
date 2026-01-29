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

# INITIALISEER WATCHLIST (Session State)
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = {}

# 2. Styling & Mobile Optimization
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
    .value { font-size: 1rem; font-weight: bold; }
    .perc-sub { font-size: 0.75rem; font-weight: bold; margin-top: 2px; }
    @media (max-width: 600px) {
        .stMetric { background: #1c2128; padding: 10px; border-radius: 8px; border: 1px solid #30363d; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Scrapers
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

# 4. Sidebar Watchlist
with st.sidebar:
    st.header("📋 Live Watchlist")
    if st.session_state.watchlist:
        # Maak DataFrame van de opgeslagen dictionary
        df_data = []
        for t, info in st.session_state.watchlist.items():
            df_data.append({
                "Ticker": t,
                "Status": info['rec'],
                "Swing": f"{info['swing']:.1f}"
            })
        
        st.table(pd.DataFrame(df_data))
        
        if st.button("Clear Watchlist"):
            st.session_state.watchlist = {}
            st.rerun()
    else:
        st.write("No stocks analyzed yet.")

# 5. Dashboard Content
st.title("🏹 AI Strategy Terminal")
ticker = st.text_input("Enter Ticker", "AAPL").upper()

if ticker:
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if not data.empty:
            curr_p = float(data['Close'].iloc[-1])
            prev_p = float(data['Close'].iloc[-2])
            change = ((curr_p / prev_p) - 1) * 100
            
            # AI & Tools berekeningen
            y = data['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (12 if pred > curr_p else -8))
            lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
            sent = get_sentiment(ticker)
            
            vola = data['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            swing = 50 + (change * 6) - (vola * 4)
            
            earn = get_earnings(ticker)
            is_urgent = any(d in earn for d in ["Jan 29", "Jan 30", "Feb 1", "Feb 2"])

            # Decision Logic
            if is_urgent: rec, col, ico = "AVOID", "status-avoid", "⚠️"
            elif (ensemble > 75 or lstm > 70) and swing > 58: rec, col, ico = "BUY", "status-buy", "🚀"
            else: rec, col, ico = "HOLD", "status-hold", "⏳"

            # UPDATE WATCHLIST (Slaat nu status en swing score op)
            st.session_state.watchlist[ticker] = {
                'rec': f"{ico} {rec}",
                'swing': swing
            }

            # UI Output
            if is_urgent:
                st.markdown(f'<div class="alert-box">🚨 EARNINGS ALERT: {earn}</div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="report-container {col}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 style='margin:0;'>{ico} {rec}</h2>
                            <p style='color:#8b949e; font-size:0.8rem; margin:4px 0;'>AI Strategy Confirmation</p>
                        </div>
                        <div style="text-align: right;">
                            <span class="value" style="font-size: 1.2rem;">${curr_p:.2f}</span><br>
                            <span style="color: {'#39d353' if change >= 0 else '#f85149'}; font-weight: bold;">{change:+.2f}%</span>
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
                            <span class="perc-sub">MARKET</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Target</span>
                            <span class="value" style="color:#39d353;">${curr_p*(1+tp_pct/100):.2f}</span>
                            <span class="perc-sub" style="color:#39d353;">+{tp_pct:.2f}%</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # AI Metrics Grid
            c1, c2 = st.columns(2)
            c1.metric("Ensemble Score", f"{ensemble}%")
            c2.metric("LSTM Trend", f"{lstm}%")
            
            c3, c4 = st.columns(2)
            c3.metric("Sentiment", f"{sent}%")
            c4.metric("Swing Score", f"{swing:.1f}")
            
            st.line_chart(data['Close'], height=250)

    except Exception as e:
        st.error(f"Analysis failed: {e}")


















