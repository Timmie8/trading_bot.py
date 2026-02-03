import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import time

# 1. Pagina Configuratie & Styling voor Contrast
st.set_page_config(page_title="AI Trader Pro - Live", layout="wide")

st.markdown("""
    <style>
    /* Achtergrond en tekst */
    .stApp { background-color: #000000 !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #333 !important; }
    h1, h2, h3, p, label, span { color: #ffffff !important; }
    
    /* Knoppen Contrast */
    .stButton>button {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
        border-radius: 4px;
        font-weight: bold;
    }
    .stButton>button:hover {
        border-color: #39d353 !important;
        color: #39d353 !important;
    }

    /* Tabel Styling */
    .stTable { 
        background-color: #0a0a0a !important; 
        color: white !important;
        border: 1px solid #333 !important;
    }
    th { background-color: #111 !important; color: #39d353 !important; }
    
    /* Input Contrast */
    input { background-color: #111 !important; color: white !important; border: 1px solid #444 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Watchlist Geheugen fix
if 'watchlist' not in st.session_state or not isinstance(st.session_state.watchlist, list):
    st.session_state.watchlist = ["AAPL", "NVDA", "TSLA", "BTC-USD"]

# 3. AI Score Berekening
def perform_ai_analysis(ticker_symbol):
    try:
        data = yf.Ticker(ticker_symbol).history(period="100d")
        if data.empty: return None
        
        curr_p = float(data['Close'].iloc[-1])
        prev_p = float(data['Close'].iloc[-2])
        change = ((curr_p / prev_p) - 1) * 100
        
        # AI Trend Voorspelling (Linear Regression)
        y = data['Close'].values.reshape(-1, 1)
        X = np.array(range(len(y))).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        pred = float(reg.predict(np.array([[len(y)]]))[0][0])
        
        # Score Logica
        ensemble_score = int(72 + (12 if pred > curr_p else -8))
        vola = data['Close'].pct_change().tail(14).std() * 100
        swing_score = round(50 + (change * 6) - (vola * 4), 1)
        
        # Advies Logica
        if ensemble_score > 75 and swing_score > 58: rec, ico = "BUY", "🚀"
        elif ensemble_score < 65: rec, ico = "AVOID", "⚠️"
        else: rec, ico = "HOLD", "⏳"
        
        return {
            "Aandeel": ticker_symbol,
            "Prijs": f"${curr_p:.2f}",
            "Change %": f"{change:+.2f}%",
            "AI Score": f"{ensemble_score}%",  # DIT IS DE ENSEMBLE SCORE
            "Swing": swing_score,              # DIT IS DE SWING SCORE
            "Status": f"{ico} {rec}"
        }
    except:
        return None

# 4. Sidebar voor Beheer
with st.sidebar:
    st.header("⚙️ Instellingen")
    multi_input = st.text_input("Voeg tickers toe (komma-gescheiden)", placeholder="AAPL, TSLA, BTC-USD")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Toevoegen"):
            if multi_input:
                new_tickers = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
                st.session_state.watchlist = list(dict.fromkeys(st.session_state.watchlist + new_tickers))
                st.rerun()
    with c2:
        if st.button("Reset"):
            st.session_state.watchlist = []
            st.rerun()

# 5. Live Dashboard Fragment
st.title("🏹 AI Strategy Terminal")

@st.fragment(run_every=10)
def live_dashboard():
    if not st.session_state.watchlist:
        st.info("Voer tickers in de sidebar in om te beginnen.")
        return

    st.write(f"⏱️ **Laatste Update:** {time.strftime('%H:%M:%S')}")
    
    results = []
    for t in st.session_state.watchlist:
        res = perform_ai_analysis(t)
        if res:
            results.append(res)
    
    if results:
        # Zet om naar DataFrame voor de tabel
        df = pd.DataFrame(results)
        
        # Toon tabel met de gevraagde AI Score kolommen
        st.table(df)
        
        # Optioneel: Visualisatie van de sterkste BUY
        top_buy = df[df['Status'].str.contains("BUY")].sort_values(by="AI Score", ascending=False)
        if not top_buy.empty:
            st.success(f"🔥 Sterkste signaal: {top_buy.iloc[0]['Aandeel']} met een AI Score van {top_buy.iloc[0]['AI Score']}")

# Start de dashboard loop
live_dashboard()























