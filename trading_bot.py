import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re

# --- 1. USER DATABASE ---
USER_DATABASE = {
    "admin@trading.nl": "Admin2026!",
    "user1@client.com": "TradeSafe88"
}

# --- 2. AUTHENTICATION ---
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if st.session_state["authenticated"]:
        return True

    st.title("🔒 Secure Access")
    e_input = st.text_input("Email")
    p_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if e_input in USER_DATABASE and USER_DATABASE[e_input] == p_input:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = e_input
            st.rerun()
        else:
            st.error("Invalid credentials")
    return False

# Stop als niet ingelogd
if check_auth():
    # --- 3. THE TRADING BOT ---
    st.set_page_config(page_title="AI Trader Pro", layout="wide")
    
    with st.sidebar:
        st.write(f"Logged in as: {st.session_state['user_email']}")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.rerun()

    st.title("🏹 AI Strategy Dashboard")
    ticker_symbol = st.text_input("Enter Ticker", "AAPL").upper()

    if ticker_symbol:
        try:
            stock = yf.Ticker(ticker_symbol)
            df = stock.history(period="100d")
            
            if df.empty:
                st.warning("No data found for this ticker. Check the symbol.")
            else:
                curr_price = float(df['Close'].iloc[-1])
                
                # Snel AI model (Linear Regression)
                y = df['Close'].values.reshape(-1, 1)
                X = np.array(range(len(y))).reshape(-1, 1)
                reg = LinearRegression().fit(X, y)
                reg_pred = float(reg.predict(np.array([[len(y)]]))[0][0])
                
                # Risk berekening
                vola = df['Close'].pct_change().tail(14).std() * 100
                sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
                tp_pct = sl_pct * 2.5
                
                # Output Card
                st.success(f"Analysis for {ticker_symbol} complete!")
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Current Price", f"${curr_price:.2f}")
                col2.metric("Stop Loss", f"${curr_price*(1-sl_pct/100):.2f}", f"-{sl_pct:.2f}%")
                col3.metric("Target", f"${curr_price*(1+tp_pct/100):.2f}", f"+{tp_pct:.2f}%")
                
                st.line_chart(df['Close'])

        except Exception as e:
            st.error(f"An error occurred: {e}")









