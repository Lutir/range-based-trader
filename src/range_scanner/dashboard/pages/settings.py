"""
Settings Page — Configure API keys and scanner thresholds.
"""

import streamlit as st
import os
from pathlib import Path


def render():
    st.title("Settings")

    # API Keys
    st.markdown("### API Keys")
    st.markdown("These are stored in your `.env` file and used for Alpaca market data.")

    env_path = Path(".env")
    current_key = os.environ.get("ALPACA_API_KEY", "")
    current_secret = os.environ.get("ALPACA_SECRET_KEY", "")

    api_key = st.text_input("ALPACA_API_KEY", value=current_key, type="password")
    api_secret = st.text_input("ALPACA_SECRET_KEY", value=current_secret, type="password")
    base_url = st.text_input("ALPACA_BASE_URL", value=os.environ.get("ALPACA_BASE_URL", "https://data.alpaca.markets"))

    if st.button("Save API Keys"):
        env_content = f"ALPACA_API_KEY={api_key}\nALPACA_SECRET_KEY={api_secret}\nALPACA_BASE_URL={base_url}\n"
        env_path.write_text(env_content)
        st.success("Saved to .env. Restart the app for changes to take effect.")

    st.markdown("---")

    # Scanner Thresholds
    st.markdown("### Scanner Thresholds")
    st.markdown("These control what gets filtered out and how scoring works.")

    st.markdown("**Liquidity Filters**")
    c1, c2 = st.columns(2)
    c1.number_input("Min Volume", value=1_000_000, step=100_000, key="min_vol")
    c2.number_input("Min Dollar Volume ($)", value=20_000_000, step=1_000_000, key="min_dv")

    st.markdown("**Structure Parameters**")
    c3, c4, c5 = st.columns(3)
    c3.number_input("Pivot Window", value=3, min_value=2, max_value=5, key="pivot")
    c4.number_input("ATR Period", value=14, min_value=5, max_value=30, key="atr_p")
    c5.number_input("ADX Period", value=14, min_value=5, max_value=30, key="adx_p")

    st.markdown("**Range Width Limits**")
    c6, c7 = st.columns(2)
    c6.number_input("Max excellent width (%)", value=12, key="max_exc_w")
    c7.number_input("Too wide threshold (%)", value=25, key="too_wide")

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **Range Scanner** is a market-structure filter that identifies stocks
    with clean range-bound behavior, classifies their current state, and
    assesses whether the broader market environment supports a trade.

    It is NOT a trading bot. The human decides whether to act.
    """)
