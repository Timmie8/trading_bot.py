import streamlit as st
import yfinance as yf
import pandas as pd
import time
import re

# 1. FORCEER THEMA EN LAYOUT (Dit moet bovenaan staan)
st.set_page_config(page_title="AI Trader Black", layout="wide")

# Harde CSS injectie voor gitzwarte achtergrond
st.markdown("""
    <style>
    /* Forceer de hoofdpagina naar zwart */
    .stApp, [data-testid="stAppViewContainer"], .main {
        background-color: #000000 !important;
        color: #ffffff !important;
    }
    /* Forceer de sidebar naar donkergrijs/zwart */
    [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
        background-color: #050505 !important;
        border-right: 1px solid #333333 !important;
    }
    /* Alle teksten wit maken */
    h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown {
        color: #ffffff !important;
    }
    /* Input velden leesbaar maken */
    input, textarea {
        background-color: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #444 !important;
    }
    /* Verberg de Streamlit branding */
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Watchlist Geheugen
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA"]

# 3. Functie voor Data
def get_data(tickers):
    results = []
    for t in tickers:
        try:
            # We halen slechts 1 minuut data op voor maximale snelheid
            tick = yf.Ticker(t)
            df = tick.history(period="1d", interval="1m")
            if not df.empty:
                last_p = df['Close'].iloc[-1]
                open_p = df['Open'].iloc[0]
                change = ((last_p - open_p) / open_p) * 100
                results.append({
                    "Aandeel": t,
                    "Prijs": f"${last_p:.2f}",
                    "Verschil %": f"{change:+.2f}%",
                    "Status": "🚀" if change >= 0 else "📉"
                })
        except:
            continue
    return pd.DataFrame(results)

# 4. Dashboard Kop
st.title("🏹 AI Strategy Terminal")

# 5. Sidebar: De Multi-Ticker Input
with st.sidebar:
    st.header("Watchlist Beheer")
    st.write("Typ tickers gescheiden door een komma:")
    
    # Gebruik een key voor de input zodat we deze makkelijk kunnen uitlezen
    raw_input = st.text_input("Bijv: AAPL, TSLA, BTC-USD", key="ticker_input")
    
    if st.button("Voeg Lijst Toe"):
        if raw_input:
            # De gevraagde functie: splitsen op de komma
            new_tickers = [t.strip().upper() for t in raw_input.split(",") if t.strip()]
            st.session_state.watchlist = list(set(st.session_state.watchlist + new_tickers))
            st.rerun()

    if st.button("Wis Alles"):
        st.session_state.watchlist = []
        st.rerun()

# 6. LIVE UPDATE GEDEELTE
# We gebruiken een lege container die we constant overschrijven
placeholder = st.empty()

# Oneindige loop voor live updates (elke 5 seconden)
while True:
    with placeholder.container():
        if st.session_state.watchlist:
            # Haal verse prijzen op
            df_live = get_data(st.session_state.watchlist)
            
            if not df_live.empty:
                st.write(f"⏱️ Live Update: {time.strftime('%H:%M:%S')}")
                
                # Toon metrics
                m_cols = st.columns(len(df_live))
                for idx, row in df_live.iterrows():
                    with m_cols[idx % len(df_live)]:
                        st.metric(row['Aandeel'], row['Prijs'], row['Verschil %'])
                
                # Toon Tabel
                st.table(df_live)
            else:
                st.warning("Geen data gevonden voor deze tickers.")
        else:
            st.info("De lijst is leeg. Voeg aandelen toe in de sidebar.")
            
    time.sleep(5) # Wacht 5 seconden voor de volgende update





















