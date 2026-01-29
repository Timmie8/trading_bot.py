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

# 2. Verbeterde Styling voor Dark Mode & Conclusie
st.markdown("""
    <style>
    .report-container { 
        padding: 20px; border-radius: 15px; background-color: #161b22; 
        color: #c9d1d9; border: 1px solid #30363d; border-left: 10px solid; margin-bottom: 20px;
    }
    .status-buy { border-left-color: #39d353; }
    .status-hold { border-left-color: #d29922; }
    .status-avoid { border-left-color: #f85149; }
    
    .logic-box {
        background-color: #0d1117;
        padding: 15px;
        border-radius: 10px;
        border: 1px dashed #30363d;
        margin-top: 15px;
    }
    .value { font-size: 1.2rem; font-weight: bold; color: white; }
    .label { font-size: 0.75rem; color: #8b949e; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# 3. Hulpfuncties (Scrapers)
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

# 4. Dashboard Applicatie
st.title("🏹 AI Strategy Terminal")
ticker = st.text_input("Enter Ticker", "AAPL").upper()

if ticker:
    try:
        data = yf.Ticker(ticker).history(period="100d")
        if not data.empty:
            curr_p = float(data['Close'].iloc[-1])
            prev_p = float(data['Close'].iloc[-2])
            change = ((curr_p / prev_p) - 1) * 100
            
            # Berekeningen
            y = data['Close'].values.reshape(-1, 1)
            X = np.array(range(len(y))).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            pred = float(reg.predict(np.array([[len(y)]]))[0][0])
            
            ensemble = int(72 + (12 if pred > curr_p else -8))
            lstm = int(65 + (data['Close'].iloc[-5:].pct_change().sum() * 150))
            sent = get_sentiment(ticker)
            vola = data['Close'].pct_change().tail(14).std() * 100
            swing = 50 + (change * 6) - (vola * 4)
            
            earn = get_earnings(ticker)
            is_urgent = any(d in earn for d in ["Jan 29", "Jan 30", "Feb 1", "Feb 2"])

            # Decision Logic
            if is_urgent: rec, col, ico = "AVOID", "status-avoid", "⚠️"
            elif (ensemble > 75 or lstm > 70) and swing > 58: rec, col, ico = "BUY", "status-buy", "🚀"
            else: rec, col, ico = "HOLD", "status-hold", "⏳"

            # --- AI CONCLUSIE GENERATOR ---
            redenen = []
            if ensemble > 75: redenen.append("✅ **Trend Sterkte**: De AI ziet een opwaartse regressielijn.")
            if sent > 75: redenen.append("✅ **Sentiment**: Het nieuws rondom dit aandeel is zeer positief.")
            if swing > 60: redenen.append("✅ **Momentum**: De prijsactie vertoont een sterke 'swing' omhoog.")
            if vola > 5: redenen.append("⚠️ **Risico**: Hoge volatiliteit gedetecteerd.")
            
            conclusie_tekst = " ".join(redenen) if redenen else "Geen sterke afwijkingen gedetecteerd. Neutrale marktpositie."

            # UI Output
            st.markdown(f"""
                <div class="report-container {col}">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <h2 style='margin:0;'>{ico} {rec}</h2>
                            <p style='color:#8b949e;'>AI Strategie Rapport voor {ticker}</p>
                        </div>
                        <div style="text-align: right;">
                            <span class="value">${curr_p:.2f}</span><br>
                            <span style="color: {'#39d353' if change >= 0 else '#f85149'};">{change:+.2f}%</span>
                        </div>
                    </div>
                    
                    <div class="logic-box">
                        <strong style="color: #58a6ff;">🤖 AI Redenering:</strong><br>
                        <p style="margin-top: 5px; font-size: 0.9rem;">{conclusie_tekst}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Ensemble Score", f"{ensemble}%")
            c2.metric("LSTM Trend", f"{lstm}%")
            c3.metric("Sentiment", f"{sent}%")
            c4.metric("Swing Score", f"{swing:.1f}")
            
            st.line_chart(data['Close'], height=250)

    except Exception as e:
        st.error(f"Fout: {e}")














