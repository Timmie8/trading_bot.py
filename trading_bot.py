import streamlit as st
import yfinance as yf
import pandas as pd
import time
import re

# 1. Pagina Configuratie
st.set_page_config(page_title="AI Trader Live", layout="wide")

# Initialiseer de lijst met tickers in het geheugen
if 'ticker_list' not in st.session_state:
    st.session_state.ticker_list = ["AAPL", "BTC-USD"]

# 2. Functie om data op te halen (Snel & Efficiënt)
def get_live_data(tickers):
    results = []
    for t in tickers:
        try:
            stock = yf.Ticker(t)
            # We pakken de allerlaatste prijs (1 dag historie, per minuut)
            data = stock.history(period="1d", interval="1m")
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                prev_close = data['Open'].iloc[0]
                change = ((current_price - prev_close) / prev_close) * 100
                results.append({
                    "Ticker": t,
                    "Prijs": round(current_price, 2),
                    "Change %": f"{change:+.2f}%",
                    "Update": time.strftime("%H:%M:%S")
                })
        except:
            continue
    return pd.DataFrame(results)

# 3. Sidebar: Meerdere aandelen tegelijk toevoegen
with st.sidebar:
    st.header("📋 Watchlist Beheer")
    new_input = st.text_area("Voer tickers in (scheid met komma's)", 
                             placeholder="bijv: AAPL, TSLA, NVDA, BTC-USD")
    
    if st.button("Voeg toe aan Watchlist"):
        # Split op komma, verwijder spaties en zet in hoofdletters
        added_tickers = [t.strip().upper() for t in new_input.split(",") if t.strip()]
        # Voeg samen met bestaande lijst en verwijder duplicaten
        st.session_state.ticker_list = list(set(st.session_state.ticker_list + added_tickers))
        st.rerun()

    if st.button("Lijst Wissen"):
        st.session_state.ticker_list = []
        st.rerun()

# 4. Het Live Gedeelte (De Fragment)
@st.fragment(run_every=10) # DIT ZORGT VOOR DE LIVE UPDATE ELKE 10 SECONDEN
def show_live_watchlist():
    st.subheader("🔄 Live Koersen (Update elke 10s)")
    if st.session_state.ticker_list:
        df = get_live_data(st.session_state.ticker_list)
        if not df.empty:
            # Weergeven als een mooie tabel
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Ook visuele kaarten voor de eerste paar
            cols = st.columns(min(len(df), 4))
            for i, row in df.iterrows():
                if i < 4:
                    with cols[i]:
                        color = "green" if "+" in row['Change %'] else "red"
                        st.metric(row['Ticker'], f"${row['Prijs']}", row['Change %'])
        else:
            st.warning("Geen data gevonden. Controleer de tickersymbolen.")
    else:
        st.info("De watchlist is leeg. Voeg tickers toe in de sidebar.")

# Activeer de live weergave
st.title("🏹 AI Strategy Terminal")
show_live_watchlist()

# 5. Overige Dashboard Content (Statisch)
st.write("---")
st.caption("De bovenstaande tabel ververst automatisch zonder de hele pagina te herladen.")




















