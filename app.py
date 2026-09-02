import streamlit as st
import pandas as pd

# Set page configurations
st.set_page_config(
    page_title="ThemaSetu - India Mutual Fund & ETF Theme Screener",
    page_icon="📊",
    layout="wide"
)

# Title & Description
st.title("🇮🇳 ThemaSetu - India Thematic Screener & Portfolio Planner")
st.markdown("""
This interactive web screening tool helps you identify, evaluate, and rank mutual fund and ETF investment themes in India. 
It uses a multi-pillar dynamic scoring model based on **Time Horizon, Macro-Regimes, and Tactical Market Sentiment**.
""")

# ==========================================
# 1. Databases & Background Rules
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

funds_db = {
    "BFSI": {
        "name": "SBI Banking & Financial Services Fund (Direct-G)",
        "aum": "₹10,105 Cr",
        "expense": "0.73%",
        "r3y": "22.87%",
        "type": "Active Sectoral Mutual Fund"
    },
    "INFRA": {
        "name": "ICICI Prudential Infrastructure Fund (Direct-G)",
        "aum": "₹8,133 Cr",
        "expense": "1.15%",
        "r3y": "26.14%",
        "type": "Active Sectoral Mutual Fund"
    },
    "GREEN": {
        "name": "SBI Energy Opportunities Fund (Direct-G)",
        "aum": "₹9,128 Cr",
        "expense": "0.80%",
        "r3y": "N/A (New)",
        "type": "Thematic Mutual Fund"
    },
    "MANU": {
        "name": "ICICI Prudential Manufacturing Fund (Direct-G)",
        "aum": "₹6,842 Cr",
        "expense": "1.18%",
        "r3y": "23.42%",
        "type": "Thematic Mutual Fund"
    },
    "TECH": {
        "name": "Tata Digital India Fund (Direct-G)",
        "aum": "₹12,255 Cr",
        "expense": "0.43%",
        "r3y": "12.91%",
        "type": "Sectoral Mutual Fund"
    },
    "DEFENSIVE": {
        "name": "Nippon India Pharma Fund (Direct-G)",
        "aum": "₹7,875 Cr",
        "expense": "0.92%",
        "r3y": "23.12%",
        "type": "Sectoral Mutual Fund"
    }
}

# ==========================================
# 2. Sidebar Settings
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
    # Short-term prioritizes Quality and Entry Price to buffer downside
    weights = {"policy": 0.15, "longevity": 0.15, "quality": 0.40, "price": 0.30}
elif "Medium-Term" in horizon:
    # Medium-term balances policies, cycles, and growth curves
    weights = {"policy": 0.30, "longevity": 0.20, "quality": 0.30, "price": 0.20}
else:
    # Long-term focuses heavily on Policy support and structural Longevity
    weights = {"policy": 0.35, "longevity": 0.35, "quality": 0.15, "price": 0.15}

# B. Determine Style Adjustments (Value vs. Momentum)
style_mults = {}
for t in themes_db:
    mult = 1.0
    if style == "Value/Contra (Unvalued & consolidating)":
        # Boost cheaper/consolidating themes
        if t["priceBase"] >= 7:
            mult = 1.10
    else: # Momentum
        # Boost themes that traditionally capture massive growth waves
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
    base_score = (t["policyBase"] * weights["policy"] + 
                  t["longevityBase"] * weights["longevity"] + 
                  t["qualityBase"] * weights["quality"] + 
                  t["priceBase"] * weights["price"])
    
    # Apply multipliers
    final_score = base_score * style_mults[t["id"]] * capex_mults[t["id"]] * sentiment_mult
    final_score = min(10.0, max(1.0, final_score)) # Clamp between 1.0 and 10.0
    
    # Categorize Action
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
# 4. Main Panel Layout
# ==========================================

# Active Scoring Weights Summary
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Policy Weight", f"{weights['policy']*100:.0f}%")
with col2:
    st.metric("Longevity Weight", f"{weights['longevity']*100:.0f}%")
with col3:
    st.metric("Quality Weight", f"{weights['quality']*100:.0f}%")
with col4:
    st.metric("Valuation/Price Weight", f"{weights['price']*100:.0f}%")

st.markdown("---")

# Leaderboard Section
st.subheader("🏆 Investment Theme Leaderboard")
st.dataframe(
    df_ranked.drop(columns=["ID", "Description"]),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# Dynamic Recommendations Block (Top 3 Scoring Themes)
st.subheader("💡 Curated Recommendations (Top 3 Scoring Themes)")
top_themes = df_ranked.head(3)

card_cols = st.columns(3)
for idx, row in top_themes.iterrows():
    theme_id = row["ID"]
    theme_name = row["Theme / Sector Name"]
    action_status = row["Tactical Action Guidance"]
    score_val = row["Final Score"]
    desc_val = row["Description"]
    
    fund = funds_db[theme_id]
    
    with card_cols[idx]:
        st.markdown(f"""
        <div style="background-color: #f1f5f9; padding: 20px; border-radius: 12px; border-left: 5px solid #1e3a8a; height: 100%; color: #1e293b;">
            <span style="font-size: 11px; font-weight: bold; color: #2563eb; text-transform: uppercase;">Rank #{idx+1} Theme</span>
            <h3 style="margin-top: 5px; color: #1e3a8a; margin-bottom: 5px;">{theme_name}</h3>
            <p style="font-size: 13px; color: #475569; margin-bottom: 10px;">{desc_val}</p>
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #cbd5e1;"/>
            <span style="font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase;">Best Fit Product Solution</span>
            <h4 style="margin-top: 2px; color: #1e293b; margin-bottom: 2px;">{fund['name']}</h4>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">({fund['type']})</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 15px; font-size: 12px; color: #334155;">
                <div><strong style="color: #0f172a;">AUM:</strong> {fund['aum']}</div>
                <div><strong style="color: #0f172a;">Expense Ratio:</strong> {fund['expense']}</div>
                <div style="grid-column: span 2;"><strong style="color: #0f172a;">3-Year CAGR:</strong> {fund['r3y']}</div>
            </div>
            <div style="margin-top: 15px; font-weight: bold; font-size: 13px; color: #0f172a;">
                Tactical Call: <span style="color: #1e3a8a;">{action_status}</span> (Score: {score_val}/10)
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Disclaimer: This tool is for educational purposes and is built to demonstrate programmatic investment screening frameworks. Please perform self-diligence before making active market investments in India.")
