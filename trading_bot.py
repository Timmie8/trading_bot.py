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

# 2. Mobiele & Alert Styling
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .report-container { 
        padding: 15px; border-radius: 12px; background-color: #161b22; 
        color: white; border-left: 6px solid; margin-bottom: 15px;
    }
    .status-buy { border-color: #39d353; }
    .status-hold { border-color: #d29922; }
    .status-avoid { border-color: #f85149; }
    
    /* De rode alert box voor Earnings */
    .alert-box { 
        background-color: rgba(248, 81, 73, 0.2); 
        color: #f85149; 
        padding: 12px; 
        border-radius: 8px; 
        margin-bottom: 15px; 
        border: 1px solid #f85149;
        font-weight: bold; 
        text-align: center;
        font-size: 0.9em;
    }

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
    .label { font-size: 0.65rem; color: #8b949e; text-transform: uppercase; display: block; }
    .value { font-size: 1rem; font-weight: bold; }
    
    @media (max-width: 600px) {
        .stMetric { background: #1c2128; padding: 10px; border-radius: 8px; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Data Functies
def get_earnings_data(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        text = soup.get_text()
        match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', text)
        return match.group(1).strip().split('-')[0].strip() if match else "N/A"
    except: return "N/A"

# 4. Main App
st.title("🏹 AI Strategy")
ticker = st.text_input("Ticker Symbol", "AAPL").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="100d")
        
        if not df.empty:
            curr_p = float(df['Close'].iloc[-1])
            change = ((curr_p / df['Close'].iloc[-2]) - 1) * 100
            
            # --- AI LOGICA ---
            vola = df['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            
            # --- EARNINGS ALERT LOGICA ---
            earnings_date = get_earnings_data(ticker)
            # Check op specifieke data voor de alert (Jan 29/30)
            is_urgent = any(d in earnings_date for d in ["Jan 29", "Jan 30", "Feb 1"])

            # Beslissing
            if is_urgent:
                rec, color, icon = "AVOID", "status-avoid", "⚠️"
                note = "Earnings coming up! High risk of gap down/up."
            elif change > 0.5:
                rec, color, icon = "BUY", "status-buy", "🚀"
                note = "Positive momentum & AI confirmed."
            else:
                rec, color, icon = "HOLD", "status-hold", "⏳"
                note = "Waiting for clearer signals."

            # --- UI OUTPUT ---
            # 1. De Alert Box (als earnings dichtbij zijn)
            if is_urgent:
                st.markdown(f'<div class="alert-box">🚨 EARNINGS ALERT: {earnings_date}<br><small>Volatility expected. Trade with caution.</small></div>', unsafe_allow_html=True)

            # 2. Hoofd Rapport
            st.markdown(f"""
                <div class="report-container {color}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 style='margin:0;'>{icon} {rec}</h2>
                            <p style='color:#8b949e; font-size:0.8rem; margin:5px 0;'>{note}</p>
                        </div>
                        <div style="text-align: right;">
                            <span class="value" style="font-size: 1.2rem;">${curr_p:.2f}</span><br>
                            <span style="color: {'#39d353' if change >= 0 else '#f85149'}; font-weight: bold;">
                                {change:+.2f}%
                            </span>
                        </div>
                    </div>
                    <div class="price-grid">
                        <div class="price-item"><span class="label">Stop Loss</span><span class="value" style="color:#f85149;">${curr_p*(1-sl_pct/100):.2f}</span></div>
                        <div class="price-item"><span class="label">Target</span><span class="value" style="color:#39d353;">${curr_p*(1+tp_pct/100):.2f}</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # 3. Ondersteunende Metrics
            c1, c2 = st.columns(2)
            c1.metric("Earnings Date", earnings_date)
            c2.metric("Volatility", f"{vola:.2f}%")
            
            st.line_chart(df['Close'], height=200)

    except Exception:
        st.error("Invalid Ticker")












