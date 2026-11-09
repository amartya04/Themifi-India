import streamlit as st
import pandas as pd
import plotly.express as px
from data_fetcher import (
    STAGE_1_THEMES,
    FUNDS_MASTER_DATA,
    HORIZON_WEIGHTS,
    compute_dynamic_score,
    fetch_live_nav_or_price,
)

st.set_page_config(
    page_title="Themifi-India | Thematic MF & ETF Screener",
    page_icon="📈",
    layout="wide",
)

# =====================================================================
# HEADER & SIDEBAR CONTROLS
# =====================================================================
st.title("📈 Themifi-India: 2-Stage Thematic Mutual Fund & ETF Screener")
st.caption(
    "Stage 1 aligns structural Indian themes with your Time Horizon & Macro Sentiment. "
    "Stage 2 scores Active Mutual Funds & Passive ETFs on a Unified Adaptive 100-Point Rubric."
)

with st.sidebar:
    st.header("⚙️ Investor Profile & Macro Inputs")

    selected_horizon = st.selectbox(
        "1. Investment Time Horizon",
        options=[
            "5+ Years (Long / Structural)",
            "3–5 Years (Medium / Cyclical)",
            "1–3 Years (Short / Tactical)",
        ],
        index=0,
    )

    sentiment_regime = st.radio(
        "2. Market Sentiment / Valuation Regime",
        options=[
            "Normal / Balanced Cycle",
            "Overheated / High Greed (Nifty P/E > 24x)",
        ],
        index=0,
        help="When Overheated is selected, +10% extra weight shifts into Downside Protection.",
    )

    vehicle_filter = st.multiselect(
        "3. Vehicle Type Filter",
        options=["Active MF", "Passive ETF"],
        default=["Active MF", "Passive ETF"],
    )

    st.subheader("📡 Live Data Controls")
    fetch_live_toggle = st.toggle(
        "Fetch Live NAV / NSE Price (mfapi.in & yfinance)",
        value=False,
        help="Enable to ping live APIs (cached for 6 hours).",
    )

    if st.button("🔄 Refresh Cache Now"):
        st.cache_data.clear()
        st.success("API Cache Cleared! Re-fetching latest NAVs & Prices...")
        st.rerun()

    st.divider()
    st.markdown("**Active Pillar Weights for Selected Horizon:**")
    w = HORIZON_WEIGHTS[selected_horizon].copy()
    if sentiment_regime == "Overheated / High Greed (Nifty P/E > 24x)":
        w["p2"] += 0.10
        w["p1"] -= 0.05
        w["p3"] -= 0.05
    st.write(f"• **P1 Long-Term Returns:** `{int(w['p1']*100)}%`")
    st.write(f"• **P2 Downside Protection:** `{int(w['p2']*100)}%`")
    st.write(f"• **P3 Recent Momentum:** `{int(w['p3']*100)}%`")
    st.write(f"• **P4 Strategy & Valuation:** `{int(w['p4']*100)}%`")
    st.write(f"• **P5 Manager / ETF Liquidity:** `{int(w['p5']*100)}%`")

# =====================================================================
# STAGE 1: TOP-DOWN THEME SCREENING
# =====================================================================
st.subheader("🧭 Stage 1: Structural Theme Ranking for Your Horizon")

theme_rows = []
for t in STAGE_1_THEMES:
    horizon_bonus = 7 if selected_horizon in t["best_horizons"] else -5
    sentiment_adj = (
        -6
        if (
            sentiment_regime == "Overheated / High Greed (Nifty P/E > 24x)"
            and "Elevated" in t["valuation_zone"]
        )
        else 0
    )
    theme_score = min(100, max(50, t["base_conviction"] + horizon_bonus + sentiment_adj))
    theme_rows.append(
        {
            "theme_id": t["theme_id"],
            "Theme Name": t["name"],
            "Focus Area": t["category"],
            "Horizon Fit Score": theme_score,
            "Macro & Structural Tailwind": t["macro_tailwind"],
            "Valuation Comfort": t["valuation_zone"],
        }
    )

df_themes = pd.DataFrame(theme_rows).sort_values(by="Horizon Fit Score", ascending=False)
st.dataframe(
    df_themes.drop(columns=["theme_id"]),
    use_container_width=True,
    hide_index=True,
)

selected_theme_names = st.multiselect(
    "🔍 Filter Stage 2 Funds by Theme (leave blank to view all 10 flagship MFs & ETFs):",
    options=df_themes["Theme Name"].tolist(),
    default=[],
)

st.divider()

# =====================================================================
# STAGE 2: BOTTOM-UP 100-POINT SCORECARD
# =====================================================================
st.subheader("🏆 Stage 2: Unified Adaptive 100-Point Fund & ETF Scorecard")

scored_funds = [
    compute_dynamic_score(f, selected_horizon, sentiment_regime)
    for f in FUNDS_MASTER_DATA
    if f["type"] in vehicle_filter
]

if selected_theme_names:
    allowed_ids = df_themes[df_themes["Theme Name"].isin(selected_theme_names)]["theme_id"].tolist()
    scored_funds = [f for f in scored_funds if f["theme_id"] in allowed_ids]

scored_funds.sort(key=lambda x: x["dynamic_score"], reverse=True)

display_rows = []
for rank, f in enumerate(scored_funds, start=1):
    live_info = (
        fetch_live_nav_or_price(f["id"], f["type"])
        if fetch_live_toggle
        else {"live_value": "Toggle Live in Sidebar", "as_of": "Nov 2026", "status": "Manual Toggle"}
    )
    display_rows.append(
        {
            "Rank": rank,
            "Scheme / ETF Name": f["name"],
            "Type": f["type"],
            "Stage 1 Theme": f["theme_label"],
            "Dynamic Score (/100)": f["dynamic_score"],
            "Base Score (/100)": f["base_score_100"],
            "Verdict Badge": f["verdict"],
            "3Y CAGR (%)": f"{f['cagr_3y']:.2f}%",
            "5Y CAGR (%)": f"{f['cagr_5y']:.2f}%" if f["cagr_5y"] else "N/A (<5Y)",
            "TER (%)": f"{f['ter_pct']:.2f}%",
            "AUM (₹ Cr)": f"₹{f['aum_cr']:,}",
            "P1: Long-Term (/25)": f["p1_long_term"],
            "P2: Downside (/25)": f["p2_downside"],
            "P3: Recent (/20)": f["p3_recent"],
            "P4: Strategy/Index (/15)": f["p4_strategy"],
            "P5: Manager/Liquidity (/15)": f["p5_execution"],
            "Guardrail Flag": f["guardrail_flag"],
            "Latest NAV / Price": live_info["live_value"],
            "Data Feed Status": live_info.get("status", "Offline"),
            "As Of Date": live_info.get("as_of", "N/A"),
        }
    )

df_scored = pd.DataFrame(display_rows)
st.dataframe(df_scored, use_container_width=True, hide_index=True)

# Visual Chart + Deep-Dive Inspector
if not df_scored.empty:
    col1, col2 = st.columns([3, 2])
    with col1:
        fig = px.bar(
            df_scored,
            x="Dynamic Score (/100)",
            y="Scheme / ETF Name",
            color="Type",
            orientation="h",
            text="Dynamic Score (/100)",
            title=f"Ranked Score for {selected_horizon}",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=420)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🔎 Deep-Dive Fund Inspector & Risk Guardrails")
        chosen_name = st.selectbox(
            "Select a Scheme or ETF:",
            options=[f["name"] for f in scored_funds],
        )
        chosen_fund = next(f for f in scored_funds if f["name"] == chosen_name)
        st.markdown(f"**Verdict:** `{chosen_fund['verdict']}`")
        st.markdown(f"**Ticker / mfapi Code:** `{chosen_fund['id']}`")
        st.markdown(f"**Manager / Index:** {chosen_fund['manager_or_index']}")
        st.markdown(f"**Guardrail Check:** `{chosen_fund['guardrail_flag']}`")
        st.info(chosen_fund["notes"])
