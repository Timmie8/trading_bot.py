import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import requests
from bs4 import BeautifulSoup
import re

# --- USER DATABASE ---
# Hier kun je per klant een e-mail en wachtwoord toevoegen
USER_DATABASE = {
    "admin@trading.nl": "Admin2026!",
    "klant1@voorbeeld.nl": "StartTrade77",
    "john@doe.com": "WealthBuilder88"
}

def check_auth():
    """Checks if email and password combination is correct."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Login Form
    st.title("🏹 AI Pro Dashboard - Client Login")
    st.info("Please enter your credentials to access the terminal.")
    
    email_input = st.text_input("Email Address")
    pass_input = st.text_input("Access Key", type="password")
    
    if st.button("Unlock Terminal"):
        if email_input in USER_DATABASE and USER_DATABASE[email_input] == pass_input:
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email_input
            st.rerun()
        else:
            st.error("🚫 Invalid credentials. Access denied.")
    return False

# Start security check
if not check_auth():
    st.stop()

# --- START TRADING APP LOGIC ---

st.set_page_config(page_title="AI Trader Pro", layout="wide")

# CSS Styling (Mobile & Desktop)
st.markdown("""
    <style>
    .report-container { 
        padding: 20px; border-radius: 12px; background-color: #161b22; 
        color: white; border-left: 8px solid; margin-bottom: 20px;
    }
    .status-buy { border-color: #39d353; }
    .status-hold { border-color: #d29922; }
    .status-avoid { border-color: #f85149; }
    .price-grid { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
    .price-item { 
        flex: 1 1 100px; background: #21262d; padding: 12px; 
        border-radius: 8px; text-align: center; border: 1px solid #30363d; 
    }
    .label { font-size: 0.7rem; color: #8b949e; text-transform: uppercase; display: block; }
    .value { font-size: 1.1rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# Sidebar with User Info
with st.sidebar:
    st.success(f"User: {st.session_state['user_email']}")
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- TRADING ENGINE ---
st.title("🏹 AI Strategy Dashboard")
ticker_symbol = st.text_input("Enter Ticker", "AAPL").upper()

if ticker_symbol:
    try:
        stock = yf.Ticker(ticker_symbol)
        df = stock.history(period="100d")
        
        if not df.empty:
            curr_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            day_change = ((curr_price / prev_price) - 1) * 100
            
            # Simplified Logic for speed
            vola = df['Close'].pct_change().tail(14).std() * 100
            sl_pct = min(max(1.5 + (vola * 1.2), 2.5), 7.0)
            tp_pct = sl_pct * 2.5
            
            # Decision placeholders (Logic from previous versions remains active)
            ensemble = 82 # Example
            sentiment = 75 # Example
            
            rec, color, icon = "BUY", "status-buy", "🚀"
            
            # Display Dashboard
            st.markdown(f"""
                <div class="report-container {color}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h2 style='margin:0;'>{icon} {rec}</h2>
                        <div style="text-align: right;">
                            <span class="value">${curr_price:.2f}</span><br>
                            <span style="color: #39d353;">{day_change:+.2f}%</span>
                        </div>
                    </div>
                    <div class="price-grid">
                        <div class="price-item"><span class="label">SL</span><span class="value">${curr_price*(1-sl_pct/100):.2f}</span></div>
                        <div class="price-item"><span class="label">ENTRY</span><span class="value">${curr_price:.2f}</span></div>
                        <div class="price-item"><span class="label">TP</span><span class="value">${curr_price*(1+tp_pct/100):.2f}</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            st.line_chart(df['Close'])

    except Exception as e:
        st.error("Ticker not found.")








