import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup

# --- Layout & Styling ---
st.set_page_config(page_title="AI Trader Dual-Logic", layout="wide")
st.markdown("""
<style>
    .status-card { padding: 20px; border-radius: 15px; margin-bottom: 20px; color: white; border-left: 10px solid; }
    .buy { background-color: #161b22; border-color: #39d353; }
    .hold { background-color: #161b22; border-color: #d29922; }
    .avoid { background-color: #161b22; border-color: #f85149; }
    .score-badge { background: #21262d; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def get_live_sentiment(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = [h.text.lower() for h in soup.find_all('h3')][:10]
        score = 70 
        for h in headlines:
            if any(w in h for w in ['growth', 'buy', 'surge', 'profit']): score += 3
            if any(w in h for w in ['drop', 'fall', 'sell', 'miss']): score -= 3
        return min(98, max(30, score))
    except: return 50

# --- App Logic ---
st.title("🏹 AI Strategy + Tier Verification")
ticker_input = st.text_input("Voer Ticker in", "AAPL").upper()

if ticker_input:
    try:
        data = yf.Ticker(ticker_input).history(period="100d")
        if not data.empty:
            curr_price = float(data['Close'].iloc[-1])
            
            # --- METHODE 1: VOLLEDIGE AI LOGICA ---
            # Linear Regression (Trend)
            y_reg = data['Close'].values.reshape(-1, 1)
            X_reg = np.array(range(len(y_reg))).reshape(-1, 1)
            model = LinearRegression().fit(X_reg, y_reg)
            pred = float(model.predict(np.array([[len(y_reg)]]))[0][0])
            
            # RSI
            delta = data['Close'].diff()
            up, down = delta.clip(lower=0), -1 * delta.clip(upper=0)
            ema_up = up.ewm(com=13, adjust=False).mean()
            ema_down = down.ewm(com=13, adjust=False).mean()
            rsi = float(100 - (100 / (1 + (ema_up / ema_down).iloc[-1])))
            
            # AI Scores berekenen (zoals in code 1)
            ensemble_score = int(72 + (12 if pred > curr_price else -8) + (10 if rsi < 45 else 0))
            last_5_days_pct = data['Close'].iloc[-5:].pct_change().sum()
            lstm_score = int(65 + (last_5_days_pct * 150))
            sentiment_score = get_live_sentiment(ticker_input)
            
            # Check of Methode 1 een BUY signaal geeft
            m1_buy_signal = (ensemble_score > 75) or (lstm_score > 70) or (sentiment_score > 75)

            # --- METHODE 2: TIER & SWING LOGICA ---
            change = ((curr_price / data['Close'].iloc[-2]) - 1) * 100
            vola = ((data['High'].iloc[-1] - data['Low'].iloc[-1]) / curr_price) * 100
            
            # Swing Score (gebaseerd op code 2)
            m2_swing_score = 50 + (change * 6) - (vola * 2)
            is_swing_valid = m2_swing_score > 60

            # --- FINALE BESLISSING ---
            if m1_buy_signal and is_swing_valid:
                res, css, icon = "BUY", "buy", "🚀"
                advies = "De AI ziet sterke patronen én de Swing-logica bevestigt het momentum."
            elif m1_buy_signal and not is_swing_valid:
                res, css, icon = "HOLD", "hold", "⏳"
                advies = "De AI is positief, maar de Swing-score is te laag (te veel risico/volatiliteit)."
            else:
                res, css, icon = "AVOID", "avoid", "⚠️"
                advies = "Geen koop-signalen van de AI methodes gevonden."

            # --- UI OUTPUT ---
            st.markdown(f"""
            <div class="status-card {css}">
                <h1>{icon} Besluit: {res}</h1>
                <p>{advies}</p>
                <hr>
                <div style="display: flex; justify-content: space-between;">
                    <span><b>Ensemble:</b> {ensemble_score}%</span>
                    <span><b>LSTM:</b> {lstm_score}%</span>
                    <span><b>Sentiment:</b> {sentiment_score}%</span>
                    <span><b>Swing Score:</b> {m2_swing_score:.1f}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.line_chart(data['Close'])
            
    except Exception as e:
        st.error(f"Fout: {e}")

