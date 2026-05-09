"""
Ticker Detail Page — Deep dive into a single stock's analysis.

Shows all scores, metrics, reason breakdown, and an inline chart.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from range_scanner.config import ScannerConfig
from range_scanner.data import fetch_bars
from range_scanner.indicators import (
    compute_adx, compute_atr_pct, compute_compression_ratio,
    compute_ema_slope_pct, compute_gap_stats,
)
from range_scanner.structure import detect_range_structure
from range_scanner.scoring import compute_score, compute_sub_scores, classify_verdict, generate_reason
from range_scanner.state import compute_position_in_range, classify_edge_position, assess_breakout_risk, compute_entry_quality
from range_scanner.models import Verdict


def render():
    st.title("Ticker Detail")
    st.markdown("Deep dive into a single ticker's range analysis.")

    ticker = st.text_input("Ticker symbol", value="ADSK").upper()
    lookback = st.slider("Lookback days", 60, 252, 120)

    if st.button("Analyze", type="primary") or ticker:
        if not ticker:
            return

        config = ScannerConfig(lookback=lookback)

        with st.spinner(f"Fetching data for {ticker}..."):
            df = fetch_bars(ticker, lookback)

        if df is None or len(df) < config.min_candles:
            st.error(f"Insufficient data for {ticker} ({len(df) if df is not None else 0} candles)")
            return

        latest_close = df["close"].iloc[-1]
        adx_series = compute_adx(df["high"], df["low"], df["close"], config.adx_period)
        adx_val = float(adx_series.iloc[-1]) if pd.notna(adx_series.iloc[-1]) else 25.0
        atr_pct = compute_atr_pct(df["high"], df["low"], df["close"], config.atr_period) or 0
        ema_slope = compute_ema_slope_pct(df["close"], config.ema_period, config.ema_slope_window) or 0.0
        gap_freq, avg_gap, max_gap = compute_gap_stats(df["open"], df["close"])
        comp_ratio, comp_label = compute_compression_ratio(df["high"], df["low"], df["close"])

        structure = detect_range_structure(df, config)

        # Header
        st.markdown(f"## {ticker} — ${latest_close:.2f}")

        if structure is None:
            st.warning("No clear range structure detected for this ticker.")
            col1, col2, col3 = st.columns(3)
            col1.metric("ADX", f"{adx_val:.1f}")
            col2.metric("ATR%", f"{atr_pct:.2f}%")
            col3.metric("EMA Slope", f"{ema_slope:.2f}%")
            return

        # Compute all metrics
        position = compute_position_in_range(latest_close, structure.support, structure.resistance)
        edge_pos = classify_edge_position(position)
        b_risk = assess_breakout_risk(df, position, structure.support, structure.resistance)
        entry_qual = compute_entry_quality(position, edge_pos, b_risk)

        avg_dollar_volume = (df["close"].iloc[-20:] * df["volume"].iloc[-20:]).mean()
        breakdown = compute_score(structure, adx_val, atr_pct, ema_slope, avg_dollar_volume, config)
        verdict = classify_verdict(breakdown.total, adx_val, ema_slope, structure.trend_leakage,
                                   structure.range_width_pct, structure.rotation_count,
                                   edge_position=edge_pos, breakout_risk=b_risk)
        struct_s, regime_s, liq_s = compute_sub_scores(breakdown)
        reason = generate_reason(structure, adx_val, ema_slope, verdict,
                                 edge_position=edge_pos, entry_quality=entry_qual, breakout_risk=b_risk)

        # Score cards
        st.markdown("### Scores")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Range Quality", f"{breakdown.total:.0f}/100")
        c2.metric("Entry Quality", f"{entry_qual:.0f}/100")
        c3.metric("Structure", f"{struct_s:.0f}/100")
        c4.metric("Regime", f"{regime_s:.0f}/100")

        # Verdict and reason
        verdict_colors = {
            "EXCELLENT_RANGE": "🟢", "RANGE_PRESSING_SUPPORT": "🔵",
            "RANGE_PRESSING_RESISTANCE": "🟠", "WATCHLIST": "🟡",
            "MESSY_RANGE": "⚪", "BROKEN_UP": "🔴", "BROKEN_DOWN": "🔴",
            "TRENDING_NOT_RANGE": "🔴", "TOO_WIDE": "🔴",
        }
        icon = verdict_colors.get(verdict.value, "⚪")
        st.markdown(f"### {icon} {verdict.value.replace('_', ' ')}")
        st.info(reason)

        # Range structure
        st.markdown("### Range Structure")
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Support", f"${structure.support:.2f}")
        r2.metric("Resistance", f"${structure.resistance:.2f}")
        r3.metric("Width", f"{structure.range_width_pct:.1f}%")
        r4.metric("Position", f"{position:.0%}")

        r5, r6, r7, r8 = st.columns(4)
        r5.metric("Rotations", structure.rotation_count)
        r6.metric("Containment", f"{structure.containment_ratio:.0%}")
        r7.metric("False Breaks", structure.resistance_false_breaks + structure.support_false_breaks)
        r8.metric("Vol Profile", structure.volume_profile)

        # Risk metrics
        st.markdown("### Risk Indicators")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Edge Position", edge_pos.value.replace("_", " "))
        k2.metric("Breakout Risk", b_risk.value)
        k3.metric("Gap Frequency", f"{gap_freq:.0%}")
        k4.metric("Compression", f"{comp_ratio:.2f} ({comp_label})")

        # Trend indicators
        st.markdown("### Trend Indicators")
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("ADX", f"{adx_val:.1f}")
        t2.metric("ATR%", f"{atr_pct:.2f}%")
        t3.metric("EMA Slope", f"{ema_slope:.2f}%")
        t4.metric("Trend Leakage", f"{structure.trend_leakage:.0%}")

        # Price chart
        st.markdown("### Price Chart")
        chart_df = df[["timestamp", "close"]].copy()
        chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])
        chart_df = chart_df.set_index("timestamp")
        chart_df["Support"] = structure.support
        chart_df["Resistance"] = structure.resistance
        chart_df["Midpoint"] = (structure.support + structure.resistance) / 2
        chart_df = chart_df.rename(columns={"close": "Price"})
        st.line_chart(chart_df[["Price", "Support", "Resistance", "Midpoint"]])

        # Score breakdown
        st.markdown("### Score Breakdown")
        score_data = {
            "Component": ["Rotation", "Reaction", "Containment", "Tightness",
                          "Range Width", "Touches (S)", "Touches (R)", "ADX",
                          "EMA Slope", "Trend Leakage", "Liquidity", "ATR"],
            "Score": [breakdown.rotation_score, breakdown.reaction_score,
                      breakdown.containment_score, breakdown.tightness_score,
                      breakdown.range_width_score, breakdown.support_touch_score,
                      breakdown.resistance_touch_score, breakdown.adx_score,
                      breakdown.ema_slope_score, breakdown.trend_leakage_score,
                      breakdown.liquidity_score, breakdown.atr_stability_score],
            "Weight": ["20%", "10%", "10%", "8%", "7%", "5%", "5%", "10%", "5%", "10%", "5%", "5%"],
        }
        st.dataframe(pd.DataFrame(score_data), use_container_width=True, hide_index=True)
