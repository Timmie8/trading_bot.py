import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re

# 1. Page Configuration (Default Dark Mode support)
st.set_page_config(page_title="AI Trader Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. Styling voor Dark Mode & UI
st.markdown("""
    <style>
    /* Algemene Dark Mode aanpassingen */
    .main { background-color: #0d1117; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Container styling */
    .report-container { 
        padding: 20px; 
        border-radius: 15px; 
        background-color: #161b22; 
        color: #c9d1d9; 
        border: 1px solid #30363d;
        border-left: 10px solid; 
        margin-bottom: 20px;
    }
    
    .status-buy { border-left-color: #39d353; box-shadow: 0 4px 15px rgba(57, 211, 83, 0.1); }
    .status-hold { border-left-color: #d29922; box-shadow: 0 4px 15px rgba(210, 153, 34, 0.1); }
    .status-avoid { border-left-color: #f85149; box-shadow: 0 4px 15px rgba(248, 81, 73, 0.1); }
    
    .alert-box { 
        background-color: rgba(248, 81, 73, 0.1); 
        color: #f85149; 
        padding: 15px; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        border: 1px solid #f85149;
        font-weight: bold; 
        text-align: center;
    }
    
    .price-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); 
        gap: 12px; 
        margin-top: 20px; 
    }
    
    .price-item { 
        background: #21262d; 
        padding: 12px; 
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #30363d; 
    }
    
    .label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; display: block; margin-bottom: 4px;}
    .value { font-size: 1.1rem; font-weight: bold; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# 3. Scrapers & Intelligence
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
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit', 'bull']): score += 3
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss', 'bear']): score -= 3
        return min(98, max(35, score))
    except: return 50

# 4. Dashboard Applicatie
st.title("🏹 AI Strategy Terminal")
ticker = st.text_input("Voer Ticker in (bijv. NVDA, TSLA, AAPL)", "AAPL").upper()

if ticker:
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if not data.empty:
            # Basis berekeningen
            curr_p = float(data['Close'].iloc[-1])
            prev_p = float(data['Close'].iloc[-2])
            change = ((curr_p / prev_p) - 1) * 100
            
            # --- AI MODELLEN & SCORES ---
            # 1. Lineaire Regressie (Trend AI)
            y = data['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            # 2. Score Berekening
            ensemble = int(72 + (12 if pred > curr_p else -8))
            lstm_sim = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
            sent = get_sentiment(ticker)
            
            # 3. Risico & Swing
            vola = data['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            swing = 50 + (change * 6) - (vola * 4)
            
            earn = get_earnings(ticker)
            is_urgent = any(d in earn for d in ["Jan 29", "Jan 30", "Feb 1", "Feb 2"])

            # Decision Logic
            if is_urgent: rec, col, ico = "AVOID", "status-avoid", "⚠️"
            elif (ensemble > 75 or lstm_sim > 70) and swing > 58: rec, col, ico = "BUY", "🚀"
            else: rec, col, ico = "HOLD", "status-hold", "⏳"
            
            # Override kleur voor BUY
            if rec == "BUY": col = "status-buy"

            # --- UI OUTPUT ---
            if is_urgent:
                st.markdown(f'<div class="alert-box">🚨 EARNINGS ALERT: {earn} - Hoog risico op volatiliteit!</div>', unsafe_allow_html=True)

            st.markdown(f"""
                <div class="report-container {col}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2 style='margin:0; color: white;'>{ico} {rec}</h2>
                            <p style='color:#8b949e; font-size:0.9rem; margin:4px 0;'>AI Strategy Intelligence Output</p>
                        </div>
                        <div style="text-align: right;">
                            <span class="value" style="font-size: 1.5rem;">${curr_p:.2f}</span><br>
                            <span style="color: {'#39d353' if change >= 0 else '#f85149'}; font-weight: bold;">{change:+.2f}%</span>
                        </div>
                    </div>
                    <div class="price-grid">
                        <div class="price-item">
                            <span class="label">Stop Loss</span>
                            <span class="value" style="color:#f85149;">${curr_p*(1-sl_pct/100):.2f}</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Entry Zone</span>
                            <span class="value" style="color:#58a6ff;">${curr_p:.2f}</span>
                        </div>
                        <div class="price-item">
                            <span class="label">Target</span>
                            <span class="value" style="color:#39d353;">${curr_p*(1+tp_pct/100):.2f}</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # AI Score Sectie (Zichtbaar maken van de technische intelligentie)
            st.subheader("📊 Technische AI Intel Score")
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                st.metric("Trend AI Score", f"{ensemble}%", help="Gebaseerd op lineaire regressie en prijsverwachting")
            with c2:
                st.metric("Momentum AI", f"{lstm_sim}%", help="Analyse van korte termijn prijsactie")
            with c3:
                st.metric("Sentiment", f"{sent}%", help="Gescreende koppen van Yahoo Finance News")
            with c4:
                st.metric("Swing Kracht", f"{swing:.1f}", help="Relatie tussen volatiliteit en dagelijkse verandering")

            st.line_chart(data['Close'], height=300)
            
    except Exception as e:
        st.error(f"Analyse mislukt voor {ticker}: {e}")
else:
    st.info("Voer een ticker symbool in om de AI analyse te starten.")














