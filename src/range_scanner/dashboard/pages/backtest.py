"""
Backtest Page — Test if the scanner's range detections actually held.

This is NOT a trading P&L backtest. It answers:
"When the scanner said 'excellent range', did price actually stay inside?"
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import csv

from range_scanner.data import fetch_bars


def render():
    st.title("Structure Backtest")
    st.markdown('<p class="subtitle">Test whether detected ranges actually held over the following days. Not a trading backtest — a structure persistence test.</p>', unsafe_allow_html=True)

    # Help
    with st.expander("What does this test?", expanded=False):
        st.markdown("""
        **The question:** "When the scanner identified a range, did price stay inside it?"

        **How it works:**
        1. Takes all tickers that scored EXCELLENT or WATCHLIST from a previous scan
        2. Looks at the NEXT N trading days after the scan
        3. Checks if all closes stayed between the detected support and resistance
        4. Reports the "hold rate" — what percentage of ranges persisted

        **Interpreting results:**
        - **70%+ held** → The scanner is finding real structure
        - **50-70% held** → Moderate accuracy, some false positives
        - **<50% held** → Scanner may be over-scoring unstable setups

        **What "MARGINAL" means:**
        Price went slightly outside (1-2%) but didn't fully break. Still counts as held.
        """)

    st.markdown("---")

    # Controls
    results_dir = Path("results")
    results_files = sorted(results_dir.glob("*.csv")) if results_dir.exists() else []

    if not results_files:
        st.markdown("""
        <div style="text-align: center; padding: 40px; background: #F5F2EE; border-radius: 12px;">
            <span style="font-size: 2rem;">◫</span>
            <h3 style="border: none;">No scan results found</h3>
            <p style="color: #7A756E;">Run a scan first to generate results, then come back here to test them.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_file = st.selectbox(
            "Results file to test",
            results_files,
            format_func=lambda x: x.name,
            help="Pick a previously generated scan results CSV.",
        )
    with col2:
        forward_days = st.slider(
            "Forward days",
            min_value=5, max_value=30, value=10,
            help="How many trading days forward to check. 10 = ~2 weeks.",
        )
    with col3:
        min_score = st.slider(
            "Min score to test",
            min_value=40, max_value=80, value=55,
            help="Only backtest tickers above this score threshold.",
        )

    if st.button("Run Backtest", type="primary"):
        with open(selected_file) as f:
            rows = list(csv.DictReader(f))

        range_verdicts = {"EXCELLENT_RANGE", "RANGE_PRESSING_RESISTANCE",
                          "RANGE_PRESSING_SUPPORT", "WATCHLIST"}
        candidates = [r for r in rows
                      if r["verdict"] in range_verdicts
                      and r.get("support") and r.get("resistance")
                      and float(r.get("score", 0)) >= min_score]

        if not candidates:
            st.warning("No qualifying range candidates found in this results file.")
            return

        st.markdown(f"Testing **{len(candidates)}** candidates (score ≥ {min_score}) over **{forward_days}** forward days...")

        progress = st.progress(0)
        results = []

        for i, row in enumerate(candidates):
            progress.progress((i + 1) / len(candidates))
            ticker = row["ticker"]
            support = float(row["support"])
            resistance = float(row["resistance"])

            df = fetch_bars(ticker, forward_days + 5)
            if df is None or len(df) < forward_days:
                continue

            forward = df.iloc[-forward_days:]
            closes = forward["close"]
            max_close = closes.max()
            min_close = closes.min()

            inside = ((closes >= support * 0.99) & (closes <= resistance * 1.01)).all()
            if inside:
                status = "HELD"
            elif max_close > resistance * 1.02:
                status = "BROKE UP"
            elif min_close < support * 0.98:
                status = "BROKE DOWN"
            else:
                status = "MARGINAL"

            results.append({
                "Ticker": ticker,
                "Score": float(row["score"]),
                "Verdict": row["verdict"].replace("_", " "),
                "Status": status,
                "Support": f"${support:.1f}",
                "Resistance": f"${resistance:.1f}",
                "Max Close": f"${max_close:.2f}",
                "Min Close": f"${min_close:.2f}",
            })

        progress.empty()

        if not results:
            st.error("No tickers had sufficient forward data for testing.")
            return

        # Results
        df_results = pd.DataFrame(results)
        held_count = df_results["Status"].isin(["HELD", "MARGINAL"]).sum()
        broke_up = df_results["Status"].eq("BROKE UP").sum()
        broke_down = df_results["Status"].eq("BROKE DOWN").sum()
        total = len(df_results)
        hold_rate = held_count / total * 100

        st.markdown("---")
        st.markdown("### Results")

        # Big metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Hold Rate", f"{hold_rate:.0f}%", help="% of ranges that price stayed inside.")
        c2.metric("Held", f"{held_count}/{total}")
        c3.metric("Broke Up", broke_up)
        c4.metric("Broke Down", broke_down)

        # Interpretation
        if hold_rate >= 70:
            st.success(f"Strong result: {hold_rate:.0f}% of detected ranges held. Scanner is identifying real structure.")
        elif hold_rate >= 50:
            st.warning(f"Moderate result: {hold_rate:.0f}% held. Some false positives — consider tightening scoring.")
        else:
            st.error(f"Weak result: {hold_rate:.0f}% held. Scanner may be over-scoring unstable setups.")

        # Detail table
        st.markdown("### Detail")
        st.dataframe(df_results, use_container_width=True, hide_index=True)
