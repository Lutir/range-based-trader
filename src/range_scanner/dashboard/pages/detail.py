"""
Ticker Detail Page — Deep dive into any single stock's full analysis.
Everything you need to understand the scanner's decision in one view.
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
from range_scanner.models import Verdict, EdgePosition


def render():
    st.title("Ticker Detail")
    st.markdown('<p class="subtitle">Deep dive into a single stock. See every score, metric, and the reasoning behind the verdict.</p>', unsafe_allow_html=True)

    # Input
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input(
            "Enter ticker symbol",
            value="ADSK",
            placeholder="AAPL",
            help="Type any stock ticker to analyze its range structure.",
        ).upper()
    with col2:
        lookback = st.select_slider(
            "Lookback period",
            options=[60, 90, 120, 150, 180, 252],
            value=120,
            help="60 = ~3 months, 120 = ~6 months, 252 = ~1 year",
        )

    if not ticker:
        return

    analyze = st.button("Analyze", type="primary")
    if not analyze and "detail_ticker" not in st.session_state:
        st.info("Enter a ticker and click Analyze to see the full breakdown.")
        return

    if analyze:
        st.session_state["detail_ticker"] = ticker
        st.session_state["detail_lookback"] = lookback

    ticker = st.session_state.get("detail_ticker", ticker)
    lookback = st.session_state.get("detail_lookback", lookback)
    config = ScannerConfig(lookback=lookback)

    with st.spinner(f"Fetching and analyzing {ticker}..."):
        df = fetch_bars(ticker, lookback)

    if df is None or len(df) < config.min_candles:
        st.error(f"Insufficient data for {ticker}. Need at least {config.min_candles} candles, got {len(df) if df is not None else 0}.")
        return

    # Compute everything
    latest_close = df["close"].iloc[-1]
    adx_series = compute_adx(df["high"], df["low"], df["close"], config.adx_period)
    adx_val = float(adx_series.iloc[-1]) if pd.notna(adx_series.iloc[-1]) else 25.0
    atr_pct = compute_atr_pct(df["high"], df["low"], df["close"], config.atr_period) or 0
    ema_slope = compute_ema_slope_pct(df["close"], config.ema_period, config.ema_slope_window) or 0.0
    gap_freq, avg_gap, max_gap = compute_gap_stats(df["open"], df["close"])
    comp_ratio, comp_label = compute_compression_ratio(df["high"], df["low"], df["close"])
    avg_dollar_volume = (df["close"].iloc[-20:] * df["volume"].iloc[-20:]).mean()

    structure = detect_range_structure(df, config)

    st.markdown("---")

    # Header with price
    st.markdown(f"""
    <div style="display: flex; align-items: baseline; gap: 16px;">
        <h1 style="margin: 0; padding: 0; border: none;">{ticker}</h1>
        <span style="font-size: 1.6rem; font-weight: 300; color: #4A4540;">${latest_close:.2f}</span>
    </div>
    """, unsafe_allow_html=True)

    if structure is None:
        st.warning("No clear range structure detected for this ticker.")
        st.markdown("### Indicators")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("ADX", f"{adx_val:.1f}", help="Trend strength. Below 20 = sideways.")
        c2.metric("ATR%", f"{atr_pct:.2f}%", help="Average daily movement as % of price.")
        c3.metric("EMA Slope", f"{ema_slope:.2f}%", help="Directional drift over 20 days.")
        c4.metric("Gap Freq.", f"{gap_freq:.0%}", help="% of days with >2% overnight gaps.")
        return

    # Full analysis
    position = compute_position_in_range(latest_close, structure.support, structure.resistance)
    edge_pos = classify_edge_position(position)
    b_risk = assess_breakout_risk(df, position, structure.support, structure.resistance)
    entry_qual = compute_entry_quality(position, edge_pos, b_risk)
    breakdown = compute_score(structure, adx_val, atr_pct, ema_slope, avg_dollar_volume, config)
    verdict = classify_verdict(breakdown.total, adx_val, ema_slope, structure.trend_leakage,
                               structure.range_width_pct, structure.rotation_count,
                               edge_position=edge_pos, breakout_risk=b_risk)
    struct_s, regime_s, liq_s = compute_sub_scores(breakdown)
    reason = generate_reason(structure, adx_val, ema_slope, verdict,
                             edge_position=edge_pos, entry_quality=entry_qual, breakout_risk=b_risk)

    # Verdict banner
    verdict_display = verdict.value.replace("_", " ")
    verdict_colors = {
        "EXCELLENT_RANGE": ("#D4EDDA", "#2D5F3B"),
        "RANGE_PRESSING_SUPPORT": ("#D1ECF1", "#0C5460"),
        "RANGE_PRESSING_RESISTANCE": ("#FFF3CD", "#664D03"),
        "WATCHLIST": ("#FFF3CD", "#664D03"),
        "BROKEN_UP": ("#F8D7DA", "#721C24"),
        "BROKEN_DOWN": ("#F8D7DA", "#721C24"),
        "TRENDING_NOT_RANGE": ("#E2E3E5", "#383D41"),
    }
    bg, fg = verdict_colors.get(verdict.value, ("#F5F2EE", "#4A4540"))

    st.markdown(f"""
    <div style="background: {bg}; color: {fg}; padding: 16px 24px; border-radius: 10px; margin: 16px 0;">
        <span style="font-weight: 600; font-size: 1.1rem;">{verdict_display}</span>
        <br><span style="font-size: 0.9rem; opacity: 0.85;">{reason}</span>
    </div>
    """, unsafe_allow_html=True)

    # AI-style narrative reasoning
    from range_scanner.reasoning import generate_narrative
    from range_scanner.models import TickerScanResult as TSR, BreakoutRisk, SetupType
    narrative_result = TSR(
        ticker=ticker, score=breakdown.total, verdict=verdict,
        entry_quality=entry_qual, position_in_range=round(position, 3),
        edge_position=edge_pos, breakout_risk=b_risk,
        support=structure.support, resistance=structure.resistance,
        range_width_pct=structure.range_width_pct,
        support_touches=structure.support_touches, resistance_touches=structure.resistance_touches,
        containment_ratio=structure.containment_ratio,
        latest_close=latest_close, rotation_count=structure.rotation_count,
        gap_frequency=round(gap_freq, 4), compression_label=comp_label,
        days_to_earnings=None, earnings_risk=None,
        short_pct_float=None, short_interest_risk=None,
    )
    narrative = generate_narrative(narrative_result)

    st.markdown("## Analysis")
    st.markdown(f"""
    <div style="background: #F5F2EE; border-left: 3px solid #5B8A72; padding: 20px 24px;
                border-radius: 0 10px 10px 0; margin: 16px 0; line-height: 1.8; color: #2D2A26; font-size: 0.95rem;">
        {narrative}
    </div>
    """, unsafe_allow_html=True)

    # Three main scores
    st.markdown("## Scores")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.metric("Range Quality", f"{breakdown.total:.0f}", help="Overall range structure score (0-100). Based on rotations, containment, width, reactions.")
    sc2.metric("Entry Quality", f"{entry_qual:.0f}", help="How actionable is this entry RIGHT NOW? High = near edge with low risk.")
    sc3.metric("Structure", f"{struct_s:.0f}", help="Sub-score: rotation + reaction + containment + tightness + width.")
    sc4.metric("Regime", f"{regime_s:.0f}", help="Sub-score: ADX + EMA slope + trend leakage. Low trend = high score.")

    # Range structure section
    st.markdown("## Range Structure")
    st.markdown("*Where are the support and resistance zones? How clean is the rotation?*")

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Support", f"${structure.support:.2f}", help="Lower boundary — where buyers tend to step in.")
    r2.metric("Resistance", f"${structure.resistance:.2f}", help="Upper boundary — where sellers tend to appear.")
    r3.metric("Width", f"{structure.range_width_pct:.1f}%", help="How wide the range is. 3-8% = ideal. >15% = too wide.")
    r4.metric("Position", f"{position:.0%}", help="Where is price now? 0% = at support, 100% = at resistance.")

    r5, r6, r7, r8 = st.columns(4)
    r5.metric("Rotations", structure.rotation_count, help="Full trips between the upper and lower thirds. More = stronger range.")
    r6.metric("Containment", f"{structure.containment_ratio:.0%}", help="% of closes inside the range. 80%+ = strong.")
    r7.metric("False Breaks", structure.resistance_false_breaks + structure.support_false_breaks,
              help="Times price poked past a zone and came back. More = zones validated.")
    r8.metric("Volume Profile", structure.volume_profile, help="Where is trading volume concentrated? BALANCED = healthy range.")

    # Position visualization
    st.markdown("### Current Position in Range")
    pos_pct = max(0, min(100, int(position * 100)))
    st.markdown(f"""
    <div style="background: #E8E4DF; border-radius: 20px; height: 30px; position: relative; margin: 12px 0;">
        <div style="background: linear-gradient(90deg, #5B8A72 0%, #FAF8F5 50%, #C27D5E 100%); border-radius: 20px; height: 30px; opacity: 0.3;"></div>
        <div style="position: absolute; left: {pos_pct}%; top: 50%; transform: translate(-50%, -50%); width: 16px; height: 16px; background: #2D2A26; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.2);"></div>
        <span style="position: absolute; left: 4px; top: 50%; transform: translateY(-50%); font-size: 0.7rem; color: #5B8A72;">Support ${structure.support:.0f}</span>
        <span style="position: absolute; right: 4px; top: 50%; transform: translateY(-50%); font-size: 0.7rem; color: #C27D5E;">Resistance ${structure.resistance:.0f}</span>
    </div>
    """, unsafe_allow_html=True)

    # Risk indicators
    st.markdown("## Risk Indicators")
    st.markdown("*Things that could make this range unreliable or dangerous to trade.*")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Edge Position", edge_pos.value.replace("_", " "), help="Which zone is price in? NEAR_SUPPORT = potential long entry area.")
    k2.metric("Breakout Risk", b_risk.value, help="Is price likely to break out? Based on volume + direction near edges.")
    k3.metric("Gap Frequency", f"{gap_freq:.0%}", help="% of days with >2% overnight gaps. High = unreliable support/resistance.")
    k4.metric("Compression", f"{comp_ratio:.2f} ({comp_label})", help="ATR(5)/ATR(20). <0.7 = volatility coiling (breakout may be imminent).")

    # Trend indicators
    st.markdown("## Trend Indicators")
    st.markdown("*Is this stock actually trending (bad for range trading) or sideways (good)?*")

    t1, t2, t3, t4 = st.columns(4)
    t1.metric("ADX", f"{adx_val:.1f}", help="Below 20 = weak trend (good). Above 30 = strong trend (bad for ranges).")
    t2.metric("ATR%", f"{atr_pct:.2f}%", help="Average daily movement. 1-6% = usable. Above 8% = too chaotic.")
    t3.metric("EMA Slope", f"{ema_slope:.2f}%", help="How much price drifted over 20 days. Near 0% = flat (good).")
    t4.metric("Trend Leakage", f"{structure.trend_leakage:.0%}", help="Are pivot highs/lows making higher-highs? High = still trending.")

    # Price chart
    st.markdown("## Price Chart")
    chart_df = df[["timestamp", "close"]].copy()
    chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])
    chart_df = chart_df.set_index("timestamp")
    chart_df["Support"] = structure.support
    chart_df["Resistance"] = structure.resistance
    chart_df["Midpoint"] = (structure.support + structure.resistance) / 2
    chart_df = chart_df.rename(columns={"close": "Price"})
    st.line_chart(chart_df[["Price", "Support", "Resistance", "Midpoint"]], height=350)

    # Score breakdown
    st.markdown("## Score Breakdown")
    st.markdown("*How each component contributed to the final range quality score.*")

    score_data = pd.DataFrame({
        "Component": ["Rotation", "Reaction Strength", "Containment", "Tightness",
                      "Range Width", "Support Touches", "Resistance Touches", "ADX",
                      "EMA Slope", "Trend Leakage", "Liquidity", "ATR Stability"],
        "Score": [breakdown.rotation_score, breakdown.reaction_score,
                  breakdown.containment_score, breakdown.tightness_score,
                  breakdown.range_width_score, breakdown.support_touch_score,
                  breakdown.resistance_touch_score, breakdown.adx_score,
                  breakdown.ema_slope_score, breakdown.trend_leakage_score,
                  breakdown.liquidity_score, breakdown.atr_stability_score],
        "Weight": ["20%", "10%", "10%", "8%", "7%", "5%", "5%", "10%", "5%", "10%", "5%", "5%"],
        "What it measures": [
            "Full oscillations between upper and lower thirds",
            "How strongly price bounces after touching a zone",
            "% of closes that stayed inside the range",
            "Whether price uses the full range (not just mid)",
            "3-8% width is ideal for trading",
            "Confirmed reactions at support zone",
            "Confirmed reactions at resistance zone",
            "Trend strength (lower = more sideways = better)",
            "Directional drift (flatter = better)",
            "Higher-highs/lows pattern (less = better)",
            "Dollar volume above threshold",
            "Daily volatility in usable range (1-6%)",
        ],
    })

    st.dataframe(
        score_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.0f"),
        },
    )
