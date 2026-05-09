"""
Backtest Page — Run structure persistence tests from the UI.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import csv

from range_scanner.data import fetch_bars


def render():
    st.title("Structure Backtest")
    st.markdown("""
    Tests whether detected ranges actually held over the next N trading days.

    **This is NOT a trading P&L backtest.** It only checks:
    "Did price stay inside the detected range?"
    """)

    # Find available results files
    results_dir = Path("results")
    results_files = list(results_dir.glob("*.csv")) if results_dir.exists() else []

    if not results_files:
        st.warning("No scan results found. Run a scan first.")
        return

    col1, col2 = st.columns(2)
    with col1:
        selected_file = st.selectbox("Results file", results_files, format_func=lambda x: x.name)
    with col2:
        forward_days = st.slider("Forward days to test", 5, 30, 10)

    if st.button("Run Backtest", type="primary"):
        with open(selected_file) as f:
            rows = list(csv.DictReader(f))

        range_verdicts = {"EXCELLENT_RANGE", "RANGE_PRESSING_RESISTANCE",
                          "RANGE_PRESSING_SUPPORT", "WATCHLIST"}
        candidates = [r for r in rows if r["verdict"] in range_verdicts
                      and r.get("support") and r.get("resistance")]

        if not candidates:
            st.warning("No range candidates found in results to backtest.")
            return

        st.markdown(f"Testing **{len(candidates)}** range candidates over **{forward_days}** forward days...")

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
                "Verdict": row["verdict"],
                "Status": status,
                "Support": support,
                "Resistance": resistance,
                "Max Close": round(max_close, 2),
                "Min Close": round(min_close, 2),
            })

        progress.empty()

        if not results:
            st.error("No tickers had sufficient forward data.")
            return

        # Summary
        df_results = pd.DataFrame(results)
        held = df_results["Status"].isin(["HELD", "MARGINAL"]).sum()
        total = len(df_results)
        hold_rate = held / total * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("Held Range", f"{held}/{total}", f"{hold_rate:.0f}%")
        c2.metric("Broke Out", df_results["Status"].eq("BROKE UP").sum())
        c3.metric("Broke Down", df_results["Status"].eq("BROKE DOWN").sum())

        # Color-code the table
        st.dataframe(df_results, use_container_width=True, hide_index=True)
