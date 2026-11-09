import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf

# =====================================================================
# STAGE 1: MACRO THEMES & HORIZON ALIGNMENT CATALOGUE
# =====================================================================
STAGE_1_THEMES = [
    {
        "theme_id": "core_compounders",
        "name": "Core All-Weather / Quality Compounders",
        "category": "Core Anchor & Multi-Cycle Compounding",
        "best_horizons": ["3–5 Years (Medium / Cyclical)", "5+ Years (Long / Structural)"],
        "base_conviction": 88,
        "macro_tailwind": "High ROE (>18%), global + domestic diversification, and cash buffers across market cycles.",
        "valuation_zone": "Fair / Comfortable (P/E ~21x)",
    },
    {
        "theme_id": "undervaluation_contra",
        "name": "Undervaluation / Balance Sheet Repair & Contra",
        "category": "Value / Margin of Safety / PSU Banking",
        "best_horizons": ["1–3 Years (Short / Tactical)", "3–5 Years (Medium / Cyclical)", "5+ Years (Long / Structural)"],
        "base_conviction": 85,
        "macro_tailwind": "Cleaned corporate & PSU bank balance sheets, low NPA ratios, and discounted P/B multiples.",
        "valuation_zone": "Attractive / Undervalued",
    },
    {
        "theme_id": "country_growth_capex",
        "name": "Country Growth & Capex / Infrastructure & PSU Energy",
        "category": "Sovereign Capex, Power, EPC & Capital Goods",
        "best_horizons": ["3–5 Years (Medium / Cyclical)", "5+ Years (Long / Structural)"],
        "base_conviction": 83,
        "macro_tailwind": "Government infrastructure outlay, power grid modernisation, and energy transition capex.",
        "valuation_zone": "Moderate (Selective Value in PSUs)",
    },
    {
        "theme_id": "future_prospects_make_in_india",
        "name": "Future Prospects / Make in India (Defence & Manufacturing)",
        "category": "Strategic Autonomy, PLI Schemes & Exports",
        "best_horizons": ["5+ Years (Long / Structural)", "1–3 Years (Short / Tactical)"],
        "base_conviction": 80,
        "macro_tailwind": "Defence indigenisation order books, PLI manufacturing incentives, and China+1 supply chains.",
        "valuation_zone": "Elevated in Defence (P/E >45x) / Fair in Broad Mfg",
    },
    {
        "theme_id": "domestic_consumption",
        "name": "Domestic Consumption & Structural Demand",
        "category": "FMCG, Auto, Telecom, Retail & Premiumisation",
        "best_horizons": ["5+ Years (Long / Structural)", "3–5 Years (Medium / Cyclical)"],
        "base_conviction": 78,
        "macro_tailwind": "Rising per-capita income, rural recovery, and low-beta defensive cash flows.",
        "valuation_zone": "Moderately Rich (Defensive Premium)",
    },
]

# =====================================================================
# STAGE 2: 10 FLAGSHIP INDIAN MFs & ETFs REFERENCE DATASET
# =====================================================================
FUNDS_MASTER_DATA = [
    {
        "id": "122639",
        "name": "Parag Parikh Flexi Cap Fund (Direct-G)",
        "type": "Active MF",
        "theme_id": "core_compounders",
        "theme_label": "Core All-Weather / Quality Compounder",
        "aum_cr": 145070,
        "ter_pct": 0.69,
        "cagr_3y": 12.32,
        "cagr_5y": 10.92,
        "manager_or_index": "Rajeev Thakkar (Tenure > 13 yrs)",
        "p1_long_term": 22,
        "p2_downside": 23,
        "p3_recent": 11,
        "p4_strategy": 13,
        "p5_execution": 14,
        "guardrail_penalty": 0,
        "guardrail_flag": "None",
        "valuation_cap": False,
        "notes": "Low beta (~0.65), strong cash/value cushion, ROE >18%, low Nifty 50 overlap.",
    },
    {
        "id": "119717",
        "name": "SBI Contra Fund (Direct-G)",
        "type": "Active MF",
        "theme_id": "undervaluation_contra",
        "theme_label": "Undervaluation / Balance Sheet / Contra",
        "aum_cr": 45068,
        "ter_pct": 0.91,
        "cagr_3y": 10.07,
        "cagr_5y": 13.53,
        "manager_or_index": "Dinesh Balachandran (Tenure > 8 yrs)",
        "p1_long_term": 21,
        "p2_downside": 21,
        "p3_recent": 13,
        "p4_strategy": 13,
        "p5_execution": 13,
        "guardrail_penalty": 0,
        "guardrail_flag": "None",
        "valuation_cap": False,
        "notes": "True contrarian balance-sheet focus with high margin of safety during drawdowns.",
    },
    {
        "id": "120594",
        "name": "ICICI Prudential Infrastructure Fund (Direct-G)",
        "type": "Active MF",
        "theme_id": "country_growth_capex",
        "theme_label": "Country Growth & Capex / Infrastructure",
        "aum_cr": 8227,
        "ter_pct": 1.31,
        "cagr_3y": 15.22,
        "cagr_5y": 18.50,
        "manager_or_index": "Ihab Dalwai & S. Naren (Co-mgr added Jun '26)",
        "p1_long_term": 22,
        "p2_downside": 19,
        "p3_recent": 12,
        "p4_strategy": 13,
        "p5_execution": 10,
        "guardrail_penalty": 0,
        "guardrail_flag": "None",
        "valuation_cap": False,
        "notes": "83 holdings across EPC, power, and capital goods; Beta 0.63, Sortino 1.07.",
    },
    {
        "id": "151750",
        "name": "HDFC Defence Fund (Direct-G)",
        "type": "Active MF",
        "theme_id": "future_prospects_make_in_india",
        "theme_label": "Future Prospect / Strategic Autonomy",
        "aum_cr": 11493,
        "ter_pct": 0.78,
        "cagr_3y": 34.76,
        "cagr_5y": None,
        "manager_or_index": "Priya Ranjan (Manager transition post-launch)",
        "p1_long_term": 18,
        "p2_downside": 12,
        "p3_recent": 17,
        "p4_strategy": 10,
        "p5_execution": 9,
        "guardrail_penalty": 0,
        "guardrail_flag": "Valuation Cap (P/E > 45x — SIP Only)",
        "valuation_cap": True,
        "notes": ">80% pure defence exposure, strong 3Y CAGR, but rich multiples trigger SIP-Only guardrail.",
    },
    {
        "id": "118834",
        "name": "Mirae Asset Great Consumer Fund (Direct-G)",
        "type": "Active MF",
        "theme_id": "domestic_consumption",
        "theme_label": "Domestic Consumption & Structural Growth",
        "aum_cr": 4455,
        "ter_pct": 0.67,
        "cagr_3y": 9.81,
        "cagr_5y": 11.36,
        "manager_or_index": "Siddhant Chhabria (Tenure > 5 yrs)",
        "p1_long_term": 18,
        "p2_downside": 19,
        "p3_recent": 12,
        "p4_strategy": 12,
        "p5_execution": 13,
        "guardrail_penalty": 0,
        "guardrail_flag": "None",
        "valuation_cap": False,
        "notes": "High ROE (>20%), low turnover (0.39x), nimble AUM, and low 0.67% Direct TER.",
    },
    {
        "id": "NIFTYBEES.NS",
        "name": "Nippon India ETF Nifty 50 BeES",
        "type": "Passive ETF",
        "theme_id": "core_compounders",
        "theme_label": "Core Benchmark / Large-Cap Anchor",
        "aum_cr": 66777,
        "ter_pct": 0.04,
        "cagr_3y": 11.80,
        "cagr_5y": 12.40,
        "manager_or_index": "Nifty 50 TRI (Tracking Error: ~0.04%)",
        "p1_long_term": 21,
        "p2_downside": 20,
        "p3_recent": 14,
        "p4_strategy": 13,
        "p5_execution": 15,
        "guardrail_penalty": 0,
        "guardrail_flag": "None",
        "valuation_cap": False,
        "notes": "Ultra-low 0.04% TER, deepest NSE ETF liquidity, and tight ~0.04% tracking error.",
    },
    {
        "id": "CPSEETF.NS",
        "name": "CPSE ETF (Nippon India)",
        "type": "Passive ETF",
        "theme_id": "country_growth_capex",
        "theme_label": "Country Growth / PSU Capex & Energy",
        "aum_cr": 18645,
        "ter_pct": 0.06,
        "cagr_3y": 18.00,
        "cagr_5y": 24.52,
        "manager_or_index": "Nifty CPSE TRI (Tracking Error: 0.23%)",
        "p1_long_term": 24,
        "p2_downside": 16,
        "p3_recent": 12,
        "p4_strategy": 10,
        "p5_execution": 14,
        "guardrail_penalty": 0,
        "guardrail_flag": "Top-4 Concentration (71% in NTPC, PowerGrid, ONGC, Coal India)",
        "valuation_cap": False,
        "notes": "Ultra-low 0.06% TER and high dividend yield, but heavily concentrated in 4 energy PSUs.",
    },
    {
        "id": "PSUBNKBEES.NS",
        "name": "Nippon India ETF Nifty PSU Bank BeES",
        "type": "Passive ETF",
        "theme_id": "undervaluation_contra",
        "theme_label": "Undervaluation / Balance Sheet Repair",
        "aum_cr": 3932,
        "ter_pct": 0.49,
        "cagr_3y": 18.83,
        "cagr_5y": 24.41,
        "manager_or_index": "Nifty PSU Bank TRI (SBI = 33.3% weight)",
        "p1_long_term": 24,
        "p2_downside": 14,
        "p3_recent": 15,
        "p4_strategy": 9,
        "p5_execution": 12,
        "guardrail_penalty": 0,
        "guardrail_flag": "Single-Stock Concentration (SBI 33.3%, Top 5 = 78.5%)",
        "valuation_cap": False,
        "notes": "Strong balance-sheet turnaround play; high cyclical beta and single-stock concentration.",
    },
    {
        "id": "MAKEINDIA.NS",
        "name": "Mirae Asset Nifty India Manufacturing ETF",
        "type": "Passive ETF",
        "theme_id": "future_prospects_make_in_india",
        "theme_label": "Future Prospect / Make in India PLI",
        "aum_cr": 252,
        "ter_pct": 0.36,
        "cagr_3y": 16.40,
        "cagr_5y": None,
        "manager_or_index": "Nifty India Manufacturing TRI (TE: 0.13%)",
        "p1_long_term": 19,
        "p2_downside": 17,
        "p3_recent": 15,
        "p4_strategy": 13,
        "p5_execution": 10,
        "guardrail_penalty": 0,
        "guardrail_flag": "Moderate AUM (₹252 Cr) — Use Limit Orders",
        "valuation_cap": False,
        "notes": "Well-capped weights across Auto, Capital Goods, Metals, and Chemicals.",
    },
    {
        "id": "CONSUMBEES.NS",
        "name": "Nippon India ETF Nifty India Consumption",
        "type": "Passive ETF",
        "theme_id": "domestic_consumption",
        "theme_label": "Domestic Consumption & Structural Demand",
        "aum_cr": 186,
        "ter_pct": 0.31,
        "cagr_3y": 13.10,
        "cagr_5y": 14.20,
        "manager_or_index": "Nifty India Consumption TRI",
        "p1_long_term": 18,
        "p2_downside": 19,
        "p3_recent": 12,
        "p4_strategy": 12,
        "p5_execution": 9,
        "guardrail_penalty": 0,
        "guardrail_flag": "Liquidity Watch (AUM ₹186 Cr — Check iNAV Spread)",
        "valuation_cap": False,
        "notes": "Defensive low-beta basket (Airtel, M&M, ITC, Titan); use limit orders on NSE.",
    },
]

# =====================================================================
# DYNAMIC TIME-HORIZON & MARKET SENTIMENT WEIGHTING ENGINE
# =====================================================================
HORIZON_WEIGHTS = {
    "1–3 Years (Short / Tactical)": {
        "p1": 0.10,
        "p2": 0.30,
        "p3": 0.35,
        "p4": 0.15,
        "p5": 0.10,
    },
    "3–5 Years (Medium / Cyclical)": {
        "p1": 0.25,
        "p2": 0.25,
        "p3": 0.20,
        "p4": 0.15,
        "p5": 0.15,
    },
    "5+ Years (Long / Structural)": {
        "p1": 0.30,
        "p2": 0.20,
        "p3": 0.10,
        "p4": 0.25,
        "p5": 0.15,
    },
}


def compute_dynamic_score(fund: dict, horizon: str, sentiment_regime: str) -> dict:
    w = HORIZON_WEIGHTS.get(horizon, HORIZON_WEIGHTS["3–5 Years (Medium / Cyclical)"]).copy()

    if sentiment_regime == "Overheated / High Greed (Nifty P/E > 24x)":
        w["p2"] += 0.10
        w["p1"] -= 0.05
        w["p3"] -= 0.05

    p1_norm = (fund["p1_long_term"] / 25.0) * 100.0
    p2_norm = (fund["p2_downside"] / 25.0) * 100.0
    p3_norm = (fund["p3_recent"] / 20.0) * 100.0
    p4_norm = (fund["p4_strategy"] / 15.0) * 100.0
    p5_norm = (fund["p5_execution"] / 15.0) * 100.0

    weighted_score = (
        p1_norm * w["p1"]
        + p2_norm * w["p2"]
        + p3_norm * w["p3"]
        + p4_norm * w["p4"]
        + p5_norm * w["p5"]
    ) - fund.get("guardrail_penalty", 0)

    final_score = round(max(0.0, min(100.0, weighted_score)), 1)
    base_score = (
        fund["p1_long_term"]
        + fund["p2_downside"]
        + fund["p3_recent"]
        + fund["p4_strategy"]
        + fund["p5_execution"]
        - fund.get("guardrail_penalty", 0)
    )

    if fund.get("valuation_cap", False):
        verdict = "Accumulate via SIP Only (Valuation Cap)"
    elif final_score >= 80:
        verdict = "High-Conviction Buy"
    elif final_score >= 65:
        if "Limit Orders" in fund["guardrail_flag"] or "Liquidity Watch" in fund["guardrail_flag"]:
            verdict = "Accumulate (Use Limit Orders)"
        else:
            verdict = "Accumulate / SIP"
    elif final_score >= 50:
        verdict = "Watchlist / Hold"
    else:
        verdict = "Avoid / Switch"

    return {
        **fund,
        "base_score_100": base_score,
        "dynamic_score": final_score,
        "verdict": verdict,
    }


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_live_nav_or_price(identifier: str, vehicle_type: str) -> dict:
    try:
        if vehicle_type == "Active MF":
            url = f"https://api.mfapi.in/mf/{identifier}"
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    latest_nav = float(data[0]["nav"])
                    latest_date = data[0]["date"]
                    return {"live_value": f"₹{latest_nav:,.2f}", "as_of": latest_date, "status": "Live (mfapi.in)"}
        else:
            ticker = yf.Ticker(identifier)
            hist = ticker.history(period="5d")
            if not hist.empty:
                last_close = float(hist["Close"].iloc[-1])
                last_date = hist.index[-1].strftime("%d-%m-%Y")
                return {"live_value": f"₹{last_close:,.2f}", "as_of": last_date, "status": "Live (NSE/yfinance)"}
    except Exception:
        pass
    return {"live_value": "Cached Reference", "as_of": "Nov 2026", "status": "Fallback Mode"}
