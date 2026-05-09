"""
Settings Page — Configure API keys and scanner thresholds.
All settings explained clearly so you know what each one does.
"""

import streamlit as st
import os
from pathlib import Path


def render():
    st.title("Settings")
    st.markdown('<p class="subtitle">Configure your API keys and scanner thresholds. Changes take effect on next scan.</p>', unsafe_allow_html=True)

    # API Keys section
    st.markdown("## API Keys")
    st.markdown("Your Alpaca credentials for fetching market data. Get a free account at [alpaca.markets](https://alpaca.markets).")

    env_path = Path(".env")
    current_key = os.environ.get("ALPACA_API_KEY", "")
    current_secret = os.environ.get("ALPACA_SECRET_KEY", "")
    current_url = os.environ.get("ALPACA_BASE_URL", "https://data.alpaca.markets")

    with st.container():
        api_key = st.text_input(
            "API Key",
            value=current_key,
            type="password",
            help="Your APCA-API-KEY-ID from Alpaca dashboard.",
        )
        api_secret = st.text_input(
            "Secret Key",
            value=current_secret,
            type="password",
            help="Your APCA-API-SECRET-KEY from Alpaca dashboard.",
        )
        base_url = st.text_input(
            "Base URL",
            value=current_url,
            help="Usually https://data.alpaca.markets. Don't change unless you know what you're doing.",
        )

        if st.button("Save API Keys"):
            env_content = f"ALPACA_API_KEY={api_key}\nALPACA_SECRET_KEY={api_secret}\nALPACA_BASE_URL={base_url}\n"
            env_path.write_text(env_content)
            st.success("Saved! Restart the app (`Ctrl+C` then rerun) for changes to take effect.")

    st.markdown("---")

    # Scanner Thresholds
    st.markdown("## Scanner Thresholds")
    st.markdown("These control what gets filtered and how strict the scoring is.")

    st.markdown("### Liquidity Filters")
    st.markdown("*Stocks below these thresholds get rejected as ILLIQUID. Higher = stricter.*")

    lc1, lc2 = st.columns(2)
    with lc1:
        st.number_input(
            "Min Average Daily Volume",
            value=1_000_000, step=500_000, format="%d",
            help="How many shares must trade per day. 1M is standard for large caps. Lower for small caps.",
            key="s_min_vol",
        )
    with lc2:
        st.number_input(
            "Min Dollar Volume ($)",
            value=20_000_000, step=5_000_000, format="%d",
            help="Shares * price per day. $20M is standard. Use $50M+ for Nasdaq-100 scans.",
            key="s_min_dv",
        )

    st.markdown("### Structure Parameters")
    st.markdown("*How the scanner detects support and resistance zones.*")

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.number_input(
            "Pivot Window",
            value=3, min_value=2, max_value=7,
            help="How many candles on each side to confirm a pivot high/low. 3 = standard. Higher = fewer but stronger pivots.",
            key="s_pivot",
        )
    with sc2:
        st.number_input(
            "ATR Period",
            value=14, min_value=5, max_value=30,
            help="Period for Average True Range calculation. 14 is industry standard.",
            key="s_atr",
        )
    with sc3:
        st.number_input(
            "ADX Period",
            value=14, min_value=5, max_value=30,
            help="Period for Average Directional Index. 14 is standard.",
            key="s_adx",
        )

    st.markdown("### Range Width Limits")
    st.markdown("*How wide a range can be before getting penalized or rejected.*")

    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        st.number_input(
            "Ideal max width (%)",
            value=8, min_value=3, max_value=15,
            help="Ranges up to this width get full score. 3-8% is the sweet spot for swing trading.",
            key="s_ideal_w",
        )
    with wc2:
        st.number_input(
            "Wide range threshold (%)",
            value=15, min_value=10, max_value=25,
            help="Ranges wider than this get capped at score 50 and labeled WIDE_RANGE.",
            key="s_wide_w",
        )
    with wc3:
        st.number_input(
            "Too wide / reject (%)",
            value=25, min_value=15, max_value=50,
            help="Ranges wider than this get capped at score 30 and labeled TOO_WIDE.",
            key="s_reject_w",
        )

    st.markdown("---")

    # Reference section
    st.markdown("## Quick Reference")

    with st.expander("What do the scores mean?"):
        st.markdown("""
        | Score | Meaning |
        |-------|---------|
        | **Range Quality (0-100)** | How clean is the rotational structure? Based on rotations, containment, width, reactions. |
        | **Entry Quality (0-100)** | Is price near a useful edge right now? 100 = at support/resistance with low breakout risk. 0 = mid-range or broken. |
        | **Context Score (0-100)** | Does the broader market/sector environment support this setup? Only available with `--context` flag. |
        """)

    with st.expander("What do the verdicts mean?"):
        st.markdown("""
        | Verdict | Meaning |
        |---------|---------|
        | EXCELLENT RANGE | Clean rotational structure, actively trading within bounds |
        | PRESSING SUPPORT | Valid range, price currently near the floor |
        | PRESSING RESISTANCE | Valid range, price currently near the ceiling |
        | WATCHLIST | Decent range structure, but not at an actionable edge |
        | WIDE RANGE | Range exists but 15-25% wide — too broad for tight trades |
        | MESSY RANGE | Weak structure, not clearly rotational |
        | BROKEN UP | Price has exited above resistance |
        | BROKEN DOWN | Price has exited below support |
        | TRENDING | Strong directional movement, not range-bound |
        | TOO WIDE | Range >25% — not useful for range trading |
        """)

    with st.expander("What is range trading?"):
        st.markdown("""
        **Range trading** = buying near support (the floor) and selling near resistance (the ceiling)
        when a stock is bouncing between two price levels.

        **It works best when:**
        - The range has been tested multiple times (many "rotations")
        - The stock is NOT trending (low ADX)
        - There's no imminent catalyst (earnings, FDA decision)
        - The broader market is calm

        **It fails when:**
        - The stock breaks out of the range (breakout)
        - Earnings or news destroy the structure
        - The market suddenly trends hard in one direction

        **This scanner helps by:** identifying which stocks are currently
        in a range-like pattern, and whether the timing is good or bad.
        """)

    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #B8B2A8; font-size: 0.8rem;">
        Range Scanner is a market structure filter. Not financial advice.<br>
        The human decides whether to act.
    </div>
    """, unsafe_allow_html=True)
