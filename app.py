import streamlit as st
import pandas as pd
import datetime
import textwrap

# Import the live data fetching module (keeps our main app modular and uncluttered!)
try:
    from data_fetcher import fetch_live_fund_data, STATIC_FUNDS_DB
except ImportError:
    try:
        from data_fetcher_v2 import fetch_live_fund_data, STATIC_FUNDS_DB
    except ImportError:
        # Safe local fallback inside the sandbox
        import sys
        sys.path.append("/workspace/scratch")
        from data_fetcher_v2 import fetch_live_fund_data, STATIC_FUNDS_DB

# Set page configurations
st.set_page_config(
    page_title="themifi-india | Dynamic Thematic Screener",
    page_icon="🇮🇳",
    layout="wide"
)

# Brand Header
st.title("📊 themifi-india")
st.subheader("Interactive Mutual Fund & ETF Theme Screener")
st.markdown("""
Welcome to **themifi-india** — an intelligent quantitative screening platform. 
This tool maps structural Indian macroeconomic trends to high-liquidity investment vehicles, dynamically scaling its analysis across **your Time Horizon, Asset Styles, and Market Sentiment**.
""")

# ==========================================
# 1. Themes Structural Database
# ==========================================
themes_db = [
    {
        "id": "BFSI",
        "name": "Banking & Financial Services (BFSI)",
        "policyBase": 7,
        "longevityBase": 7,
        "qualityBase": 10,
        "priceBase": 8,
        "capexSensitive": False,
        "desc": "Backed by exceptionally clean bank balance sheets and high credit growth in India."
    },
    {
        "id": "INFRA",
        "name": "Infrastructure & CapEx Plays",
        "policyBase": 10,
        "longevityBase": 8,
        "qualityBase": 7,
        "priceBase": 6,
        "capexSensitive": True,
        "desc": "Capitalizes on massive government public spending budget (₹11.21 Lakh Crore capex outlay)."
    },
    {
        "id": "GREEN",
        "name": "Renewable Energy & Green Transition",
        "policyBase": 9,
        "longevityBase": 10,
        "qualityBase": 6,
        "priceBase": 5,
        "capexSensitive": True,
        "desc": "Long-term megatrend capturing solar, wind, and EV ecosystem grid expansion."
    },
    {
        "id": "MANU",
        "name": "Manufacturing Renaissance",
        "policyBase": 9,
        "longevityBase": 9,
        "qualityBase": 7,
        "priceBase": 6,
        "capexSensitive": True,
        "desc": "Riding the China+1 structural wave and local defense production initiatives."
    },
    {
        "id": "TECH",
        "name": "Technology & AI Services",
        "policyBase": 8,
        "longevityBase": 8,
        "qualityBase": 8,
        "priceBase": 7,
        "capexSensitive": False,
        "desc": "Supported by safe harbor protections, data center tax holidays, and AI expansion."
    },
    {
        "id": "DEFENSIVE",
        "name": "Healthcare & Defensives",
        "policyBase": 6,
        "longevityBase": 7,
        "qualityBase": 9,
        "priceBase": 8,
        "capexSensitive": False,
        "desc": "Stable, cash-generative companies providing a risk shelter during periods of market volatility."
    }
]

# ==========================================
# 2. Sidebar Settings Control Panel
# ==========================================
st.sidebar.header("🔧 Screener Settings")

horizon = st.sidebar.selectbox(
    "1. Choose Time Horizon",
    options=["Short-Term (1-3 Years)", "Medium-Term (3-5 Years)", "Long-Term (5+ Years)"],
    index=2
)

style = st.sidebar.selectbox(
    "2. Investment Style Preference",
    options=["Momentum (Chasing strong trends)", "Value/Contra (Unvalued & consolidating)"],
    index=1
)

capex_cycle = st.sidebar.selectbox(
    "3. Macro CapEx Cycle Mode",
    options=["Expansion (High government spending)", "Slowing (Defensive/Consolidating shift)"],
    index=0
)

market_sentiment = st.sidebar.selectbox(
    "4. Tactical Market Sentiment Overlay",
    options=["Fear / Consolidation (Contrarian Accumulation)", "Neutral / Balanced", "Extreme Greed / Overheated (Tactical Caution)"],
    index=1
)

# Dynamic Tax & Friction Guidance
st.sidebar.markdown("---")
st.sidebar.subheader("💸 Taxation & Friction Summary")
if "Short-Term" in horizon:
    st.sidebar.warning("""
    ⚠️ **STCG Risk:** Gains redeemed under 12 months are taxed at **20%**. 
    Redemptions over 1 year are taxed at **12.5%** LTCG. 
    Exit loads of **1%** typically apply if exited within 365 days.
    """)
else:
    st.sidebar.success("""
    ✅ **LTCG Alignment:** Taxed at **12.5%** for gains exceeding **₹1.25 Lakhs**. 
    Exit loads (1%) are **100% avoided** since holding period is >1 year.
    """)

# ==========================================
# 3. Dynamic Calculation Engine
# ==========================================

# A. Determine Pillar Weights based on Horizon
if "Short-Term" in horizon:
    weights = {"policy": 0.15, "longevity": 0.15, "quality": 0.40, "price": 0.30}
elif "Medium-Term" in horizon:
    weights = {"policy": 0.30, "longevity": 0.20, "quality": 0.30, "price": 0.20}
else:
    weights = {"policy": 0.35, "longevity": 0.35, "quality": 0.15, "price": 0.15}

# B. Determine Style Adjustments (Value vs. Momentum)
style_mults = {}
for t in themes_db:
    mult = 1.0
    if style == "Value/Contra (Unvalued & consolidating)":
        if t["priceBase"] >= 7:
            mult = 1.10
    else: # Momentum
        if t["longevityBase"] >= 9 or t["policyBase"] >= 9:
            mult = 1.10
    style_mults[t["id"]] = mult

# C. Determine Macro CapEx Multiplier
capex_mults = {}
for t in themes_db:
    mult = 1.0
    if "Expansion" in capex_cycle:
        if t["capexSensitive"]:
            mult = 1.15  # 15% capex expansion bonus
    else: # Slowing / Defensive
        if not t["capexSensitive"]:
            mult = 1.10  # 10% defensive safety bonus
    capex_mults[t["id"]] = mult

# D. Determine Sentiment Overlay Multiplier
if "Fear" in market_sentiment:
    sentiment_mult = 1.20  # Boost contrarian entry scores
elif "Extreme Greed" in market_sentiment:
    sentiment_mult = 0.60  # Severely penalize entries due to high timing risk
else:
    sentiment_mult = 1.00

# E. Compute Final Theme Scores
ranked_data = []
for t in themes_db:
    base_score = (t["policyBase"] * weights["policy"] + \
                  t["longevityBase"] * weights["longevity"] + \
                  t["qualityBase"] * weights["quality"] + \
                  t["priceBase"] * weights["price"])
    
    final_score = base_score * style_mults[t["id"]] * capex_mults[t["id"]] * sentiment_mult
    final_score = min(10.0, max(1.0, final_score)) # Clamp between 1.0 and 10.0
    
    if final_score >= 8.5:
        action = "🟢 Strong Accumulate"
    elif final_score >= 7.0:
        action = "🟢 Accumulate / SIP"
    elif final_score >= 5.0:
        action = "🟡 Steady SIP Only"
    else:
        action = "🔴 Halt Purchases / Hold"
        
    ranked_data.append({
        "ID": t["id"],
        "Theme / Sector Name": t["name"],
        "Base Structural Score": f"{base_score:.2f}",
        "Style Adj": f"x{style_mults[t['id']]:.2f}",
        "Macro Multiplier": f"x{capex_mults[t['id']]:.2f}",
        "Sentiment Multiplier": f"x{sentiment_mult:.2f}",
        "Final Score": round(final_score, 2),
        "Tactical Action Guidance": action,
        "Description": t["desc"]
    })

# Convert to DataFrame and sort by score
df_ranked = pd.DataFrame(ranked_data).sort_values(by="Final Score", ascending=False).reset_index(drop=True)

# ==========================================
# 4. Main Dashboard Panel
# ==========================================

# Active Scoring Weights Summary Metric Bars
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Policy Focus Weight", f"{weights['policy']*100:.0f}%")
with col2:
    st.metric("Growth Longevity Weight", f"{weights['longevity']*100:.0f}%")
with col3:
    st.metric("Financial Quality Weight", f"{weights['quality']*100:.0f}%")
with col4:
    st.metric("Entry Price/Valuation Weight", f"{weights['price']*100:.0f}%")

st.markdown("---")

# Leaderboard Grid Section
st.subheader("🏆 Theme Leaderboard Ranking")
st.dataframe(
    df_ranked.drop(columns=["ID", "Description"]),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# Curated Recommendations (Top 3 Scoring Themes)
st.subheader("💡 Curated Recommendations (Top 3 Scoring Themes)")

# Data Source Status Info Alert
st.info("ℹ️ **Data Transparency Status Panel:** Recommended products load from Yahoo Finance using a local 6-hour cache. If offline, the engine activates historical fallbacks automatically.")

top_themes = df_ranked.head(3)

card_cols = st.columns(3)
current_time = datetime.datetime.now()

for idx, row in top_themes.iterrows():
    theme_id = row["ID"]
    theme_name = row["Theme / Sector Name"]
    action_status = row["Tactical Action Guidance"]
    score_val = row["Final Score"]
    desc_val = row["Description"]
    
    # FETCH REAL-TIME DATA VIA DYNAMIC API MODULAR HANDOFF
    fund = fetch_live_fund_data(theme_id)
    
    # Calculate caching age and fetch status
    status_label = "⚠️ Fallback (Stale Data)"
    status_color = "#ea580c" # Orange
    status_desc = "Offline mode. Showing static research database."
    
    if fund.get("is_live", False):
        fetched_at_str = fund.get("fetched_at", "")
        try:
            fetched_time = datetime.datetime.strptime(fetched_at_str, "%Y-%m-%d %H:%M:%S")
            time_diff_sec = (current_time - fetched_time).total_seconds()
        except Exception:
            time_diff_sec = 0
            
        if time_diff_sec > 5:
            status_label = "⚡ Cached (Live)"
            status_color = "#2563eb" # Blue
            status_desc = f"Loaded from cache (Age: {int(time_diff_sec)}s)."
        else:
            status_label = "🟢 Newly Fetched (Live)"
            status_color = "#16a34a" # Green
            status_desc = "Directly retrieved from live API."
    else:
        fetched_at_str = fund.get("fetched_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Generate daily price movement tag
    price_tracker_html = ""
    if fund["price"] != "N/A":
        color_class = "green" if fund["change_pct"] >= 0 else "red"
        symbol = "+" if fund["change_pct"] >= 0 else ""
        price_tracker_html = f"""
        <div style="font-size: 13px; color: #334155; margin-top: 5px;">
            <strong>Live Price (NAV):</strong> {fund['price']} 
            <span style="color: {color_class}; font-weight: bold; margin-left: 5px;">
                ({symbol}{fund['change_pct']}%)
            </span>
        </div>
        """
    else:
        price_tracker_html = """
        <div style="font-size: 13px; color: #64748b; margin-top: 5px;">
            <strong>Price (NAV):</strong> Fetching live update...
        </div>
        """
        
    price_tracker_clean = " ".join(price_tracker_html.split())
    
    # Build Status Block HTML
    status_block_html = f"""
    <div style="font-size: 11px; margin-top: 8px; display: flex; flex-direction: column; gap: 2px;">
        <div style="display: flex; align-items: center; gap: 5px;">
            <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background-color: {status_color};"></span>
            <strong style="color: {status_color}; font-weight: 700;">{status_label}</strong>
        </div>
        <div style="color: #64748b; font-size: 10px; padding-left: 13px; line-height: 1.3;">
            Last Fetched: {fetched_at_str} <br/>
            {status_desc}
        </div>
    </div>
    """
    status_block_clean = " ".join(status_block_html.split())
    
    with card_cols[idx]:
        card_html = f"""
        <div style="background-color: #f8fafc; padding: 22px; border-radius: 14px; border-left: 6px solid #1e3a8a; height: 100%; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); text-align: left;">
            <span style="font-size: 11px; font-weight: 700; color: #2563eb; text-transform: uppercase; letter-spacing: 0.05em;">Rank #{idx+1} Theme</span>
            <h3 style="margin-top: 5px; color: #1e3a8a; font-size: 18px; font-weight: 800; line-height: 1.3; margin-bottom: 5px;">{theme_name}</h3>
            <p style="font-size: 13px; color: #475569; margin-top: 6px; line-height: 1.5; margin-bottom: 10px;">{desc_val}</p>
            <hr style="margin: 16px 0; border: none; border-top: 1px solid #e2e8f0;"/>
            <span style="font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">Best Fit Product Solution</span>
            <h4 style="margin-top: 3px; color: #0f172a; font-size: 15px; font-weight: 700; margin-bottom: 2px;">{fund['name']}</h4>
            <div style="font-size: 11px; color: #64748b; font-weight: 500; margin-top: 1px; margin-bottom: 8px;">({fund['type']})</div>
            
            {price_tracker_clean}
            {status_block_clean}
            
            <div style="display: grid; grid-template-columns: 1fr; gap: 6px; margin-top: 14px; padding: 12px; background-color: #f1f5f9; border-radius: 8px; font-size: 12px; color: #1e293b;">
                <div><strong style="color: #0f172a;">AUM Footprint:</strong> {fund['aum']}</div>
                <div><strong style="color: #0f172a;">Expense Ratio:</strong> {fund['expense']}</div>
                <div><strong style="color: #0f172a;">3-Year CAGR:</strong> <span style="color: #0f172a; font-weight: bold;">{fund['r3y']}</span></div>
            </div>
            
            <div style="margin-top: 16px; font-size: 13px; font-weight: 800; color: #0f172a; border-top: 1px dashed #cbd5e1; padding-top: 12px;">
                Tactical Call: <span style="color: #1e3a8a;">{action_status}</span> 
                <div style="font-size: 11px; font-weight: 500; color: #64748b; margin-top: 2px;">Score: {score_val:.2f}/10</div>
            </div>
        </div>
        """
        # Collapse all newlines and indentation in card_html to 100% prevent Markdown code-block triggers!
        card_html_clean = " ".join(card_html.split())
        st.markdown(card_html_clean, unsafe_allow_html=True)

st.markdown("---")
st.caption("Disclaimer: This tool is for educational purposes and is built to demonstrate programmatic investment screening frameworks. Please perform self-diligence before making active market investments in India.")
