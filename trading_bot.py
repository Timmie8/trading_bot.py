import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# --- Configuratie ---
st.set_page_config(page_title="AI Trading Bot v2", layout="wide")

# CSS voor de Tiers (geïnspireerd op je tweede code)
st.markdown("""
<style>
    .tier-card { padding: 20px; border-radius: 10px; border-left: 10px solid; margin-bottom: 20px; background-color: #161b22; color: white; }
    .tier-A { border-color: #39d353; }
    .tier-B { border-color: #58a6ff; }
    .tier-C { border-color: #d29922; }
    .tier-D { border-color: #f85149; }
    .price-box { font-family: monospace; font-size: 1.2em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Functies uit Code 1 ---
def get_earnings_date_live(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        if "Earnings Date" in page_text:
            match = re.search(r'Earnings Date([A-Za-z0-9\s,]+)', page_text)
            if match:
                return match.group(1).strip().split('-')[0].strip()
        return None
    except: return None

def get_live_sentiment(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/news"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        headlines = [h.text.lower() for h in soup.find_all('h3')][:10]
        if not headlines: return 50, "NEUTRAL"
        pos_words = ['growth', 'buy', 'up', 'surge', 'profit', 'positive', 'beat', 'bull', 'strong', 'upgrade']
        neg_words = ['drop', 'fall', 'sell', 'loss', 'negative', 'miss', 'bear', 'weak', 'risk', 'downgrade']
        score = 70 
        for h in headlines:
            for word in pos_words:
                if word in h: score += 3
            for word in neg_words:
                if word in h: score -= 3
        return min(98, max(30, score)), ("POSITIVE" if score > 70 else "NEGATIVE" if score < 45 else "NEUTRAL")
    except: return 50, "UNAVAILABLE"

# --- Main App ---
st.title("🏹 AI Trading Bot: Strategy & Risk Integration")
ticker_input = st.text_input("Voer Ticker in (bijv. NVDA, AAPL)", "AAPL").upper()

if ticker_input:
    try:
        # 1. Data ophalen
        ticker_obj = yf.Ticker(ticker_input)
        data = ticker_obj.history(period="100d")
        
        if data.empty:
            st.error("Geen data gevonden.")
        else:
            current_price = float(data['Close'].iloc[-1])
            
            # --- Berekeningen Code 1 ---
            # ATR voor volatiliteit
            high_low = data['High'] - data['Low']
            atr = high_low.rolling(14).mean().iloc[-1]
            volatility_perc = (atr / current_price) * 100

            # RSI & Regressie
            delta = data['Close'].diff()
            up, down = delta.clip(lower=0), -1 * delta.clip(upper=0)
            ema_up = up.ewm(com=13, adjust=False).mean()
            ema_down = down.ewm(com=13, adjust=False).mean()
            rsi = float(100 - (100 / (1 + (ema_up / ema_down).iloc[-1])))
            
            y_reg = data['Close'].values.reshape(-1, 1)
            X_reg = np.array(range(len(y_reg))).reshape(-1, 1)
            model = LinearRegression().fit(X_reg, y_reg)
            pred_price = float(model.predict(np.array([[len(y_reg)]]))[0][0])

            # Scores
            sentiment_score, sentiment_status = get_live_sentiment(ticker_input)
            
            # Aantal BUY signalen tellen van Code 1
            buy_signals = 0
            if pred_price > current_price: buy_signals += 1
            if rsi < 45: buy_signals += 1
            if sentiment_score > 75: buy_signals += 1
            
            # --- Logica Code 2: Risk & Tier Systeem ---
            # Score berekening gebaseerd op Code 2 logica
            price_change = ((current_price / data['Close'].iloc[-2]) - 1) * 100
            risk_score = 50 + (price_change * 6) - (volatility_perc * 2)
            risk_score = min(max(risk_score, 1), 99)

            # Dynamische Stoploss en Target (1.5x vola stop, 2.3 RR)
            dyn_stop_perc = min(max(volatility_perc * 1.5, 2.0), 6.0)
            dyn_target_perc = dyn_stop_perc * 2.3
            
            stop_price = current_price * (1 - dyn_stop_perc/100)
            target_price = current_price * (1 + dyn_target_perc/100)

            # Tier bepaling
            if risk_score > 75 and volatility_perc < 4 and buy_signals >= 2:
                tier, status, t_color, t_msg = "A", "BUY (SWING)", "tier-A", "Perfecte setup, momentum is krachtig."
            elif risk_score > 60 and buy_signals >= 1:
                tier, status, t_color, t_msg = "B", "BUY (SWING)", "tier-B", "Trend sterk, let op de pullbacks."
            elif risk_score < 40 or volatility_perc > 7:
                tier, status, t_color, t_msg = "D", "AVOID", "tier-D", "Trend onzeker of te volatiel. Vermijd."
            else:
                tier, status, t_color, t_msg = "C", "HOLD", "tier-C", "Geen duidelijk signaal, wacht af."

            # --- Visuele Weergave ---
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                <div class="tier-card {t_color}">
                    <h3>Tier {tier}: {status}</h3>
                    <p><i>{t_msg}</i></p>
                    <hr>
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <small>HUIDIGE PRIJS</small><br>
                            <span class="price-box">${current_price:.2f}</span>
                        </div>
                        <div>
                            <small style="color: #f85149;">AI STOPLOSS</small><br>
                            <span class="price-box" style="color: #f85149;">${stop_price:.2f} (-{dyn_stop_perc:.1f}%)</span>
                        </div>
                        <div>
                            <small style="color: #39d353;">AI TARGET</small><br>
                            <span class="price-box" style="color: #39d353;">${target_price:.2f} (+{dyn_target_perc:.1f}%)</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.line_chart(data['Close'])

            with col2:
                st.subheader("Analyse Details")
                st.write(f"**Sentiment:** {sentiment_status} ({sentiment_score}%)")
                st.write(f"**RSI:** {rsi:.1f}")
                st.write(f"**Volatiliteit:** {volatility_perc:.2f}%")
                st.write(f"**Regressie Target:** ${pred_price:.2f}")
                
                earnings_date = get_earnings_date_live(ticker_input)
                if earnings_date:
                    st.warning(f"📅 Earnings: {earnings_date}")

    except Exception as e:
        st.error(f"Fout bij verwerken: {e}")
