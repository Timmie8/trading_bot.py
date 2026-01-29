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

# 2. Verbeterde Mobiele Styling
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Container aanpassingen voor mobiel */
    .report-container { 
        padding: 15px; border-radius: 12px; background-color: #161b22; 
        color: white; border-left: 6px solid; margin-bottom: 15px;
    }
    
    /* Responsive Grid: 3 kolommen op desktop, 1 of 2 op mobiel */
    .price-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); 
        gap: 10px; 
        margin-top: 15px; 
    }
    
    .price-item { 
        background: #21262d; padding: 10px; 
        border-radius: 8px; text-align: center; border: 1px solid #30363d; 
    }
    
    .label { font-size: 0.65rem; color: #8b949e; text-transform: uppercase; display: block; margin-bottom: 4px; }
    .value { font-size: 1rem; font-weight: bold; }
    .perc { font-size: 0.75rem; display: block; margin-top: 2px; }
    
    /* Specifieke mobiele optimalisaties */
    @media (max-width: 640px) {
        .report-container h2 { font-size: 1.2rem !important; }
        .value { font-size: 0.9rem !important; }
        .stMetric { background: #161b22; padding: 10px; border-radius: 10px; margin-bottom: 5px; }
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
        return match.group(1).strip().split('-')[0].strip() if match else "N/A"
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
st.title("🏹 AI Strategy")
ticker_symbol = st.text_input("Symbol", "AAPL").upper() # Korter label voor mobiel

if ticker_symbol:
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="100d")
        
        if not df.empty:
            curr_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            day_change = ((curr_price / prev_price) - 1) * 100
            
            # --- AI & RISK LOGICA ---
            y = df['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            reg_pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (12 if reg_pred > curr_price else -8))
            lstm_trend = int(65 + (df['Close'].iloc[-5:].pct_change().sum() * 150))
            sentiment = get_sentiment_score(ticker_symbol)
            
            vola = df['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            swing_score = 50 + (day_change * 6) - (vola * 4)
            
            earnings_date = get_earnings_data(ticker_symbol)
            is_earnings_urgent = "Jan 29" in earnings_date or "Jan 30" in earnings_date

            # Decision Engine
            m1_buy = (ensemble > 75) or (lstm_trend > 70) or (sentiment > 75)
            m2_buy = swing_score > 58

            if is_earnings_urgent:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "Earnings volatility expected."
            elif m1_buy and m2_buy:
                rec, color, icon = "BUY", "status-buy", "🚀"
                note = "AI & Swing confirmed."
            elif m1_buy and not m2_buy:
                rec, color, icon = "HOLD", "status-hold", "⏳"
                note = "AI positive, waiting for swing."
            else:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "No patterns detected."

            # UI Display
            st.markdown(f"""
                <div class="report-container {color}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <h2 style='margin:0; font-size: 1.4rem;'>{icon} {rec}</h2>
                            <p style='color:#8b949e; font-size:0.8rem; margin: 5px 0;'>{note}</p>
                        </div>
                        <div style="text-align: right;">
                            <span class="value" style="font-size: 1.2rem;">${curr_price:.2f}</span><br>
                            <span style="color: {'#39d353' if day_change >= 0 else '#f85149'}; font-size: 0.85em; font-weight: bold;">
                                {day_change:+.2f}%
                            </span>
                        </div>
                    </div>
                    <div style='font-size:0.75rem; margin-top: 10px;'>📅 Earnings: <b>{earnings_date}</b></div>
                    <div class="price-grid">
                        <div class="price-item">
                            <span class="label">Stop Loss</span>
                            <span class="value" style="color:#f85149;">${curr_price*(1-sl_pct/100):.2f}</span>
                            <span class="perc" style="color:#f85149;">-{sl_pct:.1f}%</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Target</span>
                            <span class="value" style="color:#39d353;">${curr_price*(1+tp_pct/100):.2f}</span>
                            <span class="perc" style="color:#39d353;">+{tp_pct:.1f}%</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Metrics (Streamlit metrics passen zich automatisch aan naar 2x2 op mobiel)
            c1, c2 = st.columns(2)
            c1.metric("AI Score", f"{ensemble}%")
            c2.metric("Sentiment", f"{sentiment}%")
            
            c3, c4 = st.columns(2)
            c3.metric("LSTM", f"{lstm_trend}%")
            c4.metric("Swing", f"{swing_score:.1f}")
            
            st.line_chart(df['Close'], height=200)

    except Exception as e:
        st.error("Error analyzing ticker.")











