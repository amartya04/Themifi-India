import streamlit as st
import pandas as pd
import numpy as np

# Try importing yfinance. If not installed in the deployment environment, we handle it gracefully.
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Robust Static Fallback Database (Our golden source from our research)
STATIC_FUNDS_DB = {
    "BFSI": {
        "name": "SBI Banking & Financial Services Fund (Direct-G)",
        "ticker": "0P0000XVZ1.BO", # Yahoo ticker for SBI Banking & Financial Services Fund Direct Growth
        "backup_ticker": "BANKBEES.NS", # ETF alternative
        "aum": "₹10,105 Cr",
        "expense": "0.73%",
        "r3y": "22.87%",
        "type": "Active Sectoral Mutual Fund"
    },
    "INFRA": {
        "name": "ICICI Prudential Infrastructure Fund (Direct-G)",
        "ticker": "0P0000XVUR.BO", # ICICI Pru Infra Direct Growth
        "backup_ticker": "INFRAIETF.NS", # ETF alternative
        "aum": "₹8,133 Cr",
        "expense": "1.15%",
        "r3y": "26.14%",
        "type": "Active Sectoral Mutual Fund"
    },
    "GREEN": {
        "name": "SBI Energy Opportunities Fund (Direct-G)",
        "ticker": "SBIEOP-DG.BO", # New fund
        "backup_ticker": "TATAPOWER.NS", # For sector proxy tracking if fund is too new
        "aum": "₹9,128 Cr",
        "expense": "0.80%",
        "r3y": "N/A (New)",
        "type": "Thematic Mutual Fund"
    },
    "MANU": {
        "name": "ICICI Prudential Manufacturing Fund (Direct-G)",
        "ticker": "0P000188S6.BO", # ICICI Pru Manufacturing Direct Growth
        "backup_ticker": "MAAMFE.NS", # Mirae Asset Manufacturing ETF
        "aum": "₹6,842 Cr",
        "expense": "1.18%",
        "r3y": "23.42%",
        "type": "Thematic Mutual Fund"
    },
    "TECH": {
        "name": "Tata Digital India Fund (Direct-G)",
        "ticker": "0P00016N7V.BO", # Tata Digital India Direct Growth
        "backup_ticker": "NETFIT.NS", # Nifty IT ETF alternative
        "aum": "₹12,255 Cr",
        "expense": "0.43%",
        "r3y": "12.91%",
        "type": "Sectoral Mutual Fund"
    },
    "DEFENSIVE": {
        "name": "Nippon India Pharma Fund (Direct-G)",
        "ticker": "0P0000XVYQ.BO", # Nippon India Pharma Direct Growth
        "backup_ticker": "PHARMABEES.NS", # Pharma ETF alternative
        "aum": "₹7,875 Cr",
        "expense": "0.92%",
        "r3y": "23.12%",
        "type": "Sectoral Mutual Fund"
    }
}

@st.cache_data(ttl=21600) # Cache the live data for 6 hours to prevent hitting APIs on every click
def fetch_live_fund_data(theme_id):
    """
    Fetches real-time price and historical performance metrics using Yahoo Finance.
    Includes an automatic fallback to pre-verified research data if offline or if tickers error out.
    """
    fund_info = STATIC_FUNDS_DB.get(theme_id)
    if not fund_info:
        return None

    # Initialize return data with our robust static defaults
    result = {
        "name": fund_info["name"],
        "type": fund_info["type"],
        "aum": fund_info["aum"],
        "expense": fund_info["expense"],
        "price": "N/A",
        "change_pct": 0.0,
        "r3y": fund_info["r3y"],
        "is_live": False
    }

    if not YFINANCE_AVAILABLE:
        return result

    # Primary and secondary tickers to try
    tickers_to_try = [fund_info["ticker"], fund_info["backup_ticker"]]

    for ticker in tickers_to_try:
        if not ticker:
            continue
        try:
            # Fetch data with yfinance
            stock = yf.Ticker(ticker)
            
            # Fetch current day's or last closing price and percent change
            history = stock.history(period="5d")
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                prev_price = history['Close'].iloc[-2] if len(history) > 1 else current_price
                change = ((current_price - prev_price) / prev_price) * 100
                
                result["price"] = f"₹{current_price:.2f}"
                result["change_pct"] = round(change, 2)
                result["is_live"] = True
                
                # Dynamic 3-Year CAGR Calculation if historical data is available
                # 3 years corresponds to ~756 trading days
                history_3y = stock.history(period="3y")
                if len(history_3y) > 500: # Ensure we have adequate history
                    start_val = history_3y['Close'].iloc[0]
                    end_val = history_3y['Close'].iloc[-1]
                    years = (history_3y.index[-1] - history_3y.index[0]).days / 365.25
                    
                    if start_val > 0:
                        cagr = ((end_val / start_val) ** (1 / years) - 1) * 100
                        result["r3y"] = f"{cagr:.2f}%"
                break # If successful, stop trying tickers
                
        except Exception:
            # Squelch and fall back to the next ticker or static data
            continue

    return result
