import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 1. Pagina Configuratie & Zwarte Achtergrond
st.set_page_config(page_title="AI Trader Black Edition", layout="wide")

# Custom CSS voor een gitzwarte achtergrond en strakke look
st.markdown("""
    <style>
    /* Hoofdpagina zwart maken */
    .stApp {
        background-color: #000000;
        color: #ffffff;
    }
    /* Sidebar zwart maken */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a;
        border-right: 1px solid #333;
    }
    /* Tekstkleuren aanpassen voor leesbaarheid */
    h1, h2, h3, p, span {
        color: #ffffff !important;
    }
    /* Dataframe styling */
    .stDataFrame {
        background-color: #111111;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Geheugen voor de watchlist
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA"]

# 3. Functie voor Live Data
def fetch_live_prices(ticker_list):
    data_list = []
    for t in ticker_list:
        try:
            ticker = yf.Ticker(t)
            # Haal de meest recente prijs op (1 minuut interval)
            df = ticker.history(period="1d", interval="1m")
            if not df.empty:
                price = df['Close'].iloc[-1]
                change = ((price - df['Open'].iloc[0]) / df['Open'].iloc[0]) * 100
                data_list.append({
                    "Ticker": t,
                    "Prijs": f"${price:.2f}",
                    "Verschil": f"{change:+.2f}%",
                    "Status": "🟢" if change >= 0 else "🔴"
                })
        except:
            continue
    return pd.DataFrame(data_list)

# 4. Sidebar: Meerdere tickers invoeren
with st.sidebar:
    st.header("🎮 Controle Paneel")
    
    # Gebruik een tekstveld voor directe invoer
    multi_input = st.text_input("Voeg tickers toe (bijv: AAPL, TSLA, BTC-USD)", "")
    
    if st.button("Toevoegen"):
        if multi_input:
            # Splitsen op komma en schoonmaken
            new_tickers = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
            # Toevoegen aan de lijst en dubbelen verwijderen
            st.session_state.watchlist = list(set(st.session_state.watchlist + new_tickers))
            st.success(f"{len(new_tickers)} ticker(s) toegevoegd!")
            st.rerun()

    if st.button("Lijst Wissen"):
        st.session_state.watchlist = []
        st.rerun()

# 5. Live Dashboard (Update Fragment)
st.title("🏹 AI Strategy Terminal - Live")

@st.fragment(run_every=10)
def live_watchlist_component():
    if st.session_state.watchlist:
        st.write(f"⏱️ Laatste live update: {time.strftime('%H:%M:%S')}")
        
        # Haal data op
        df_live = fetch_live_prices(st.session_state.watchlist)
        
        if not df_live.empty:
            # Toon metrics bovenaan
            cols = st.columns(len(df_live))
            for i, row in df_live.iterrows():
                with cols[i]:
                    st.metric(row['Ticker'], row['Prijs'], row['Verschil'])
            
            # Toon de volledige tabel
            st.write("### 📈 Markt Overzicht")
            st.dataframe(df_live, use_container_width=True, hide_index=True)
        else:
            st.warning("Wachten op data van Yahoo Finance...")
    else:
        st.info("Voeg tickers toe via de sidebar om te beginnen.")

# Roep de fragment-functie aan
live_watchlist_component()





















