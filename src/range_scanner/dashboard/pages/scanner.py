"""
Scanner Page — Run scans and view ranked results.

This is the main page. Pick a universe, set filters, click scan.
Results show up as an interactive table you can sort and filter.
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
from range_scanner.models import TickerScanResult, Verdict, EdgePosition, BreakoutRisk
from range_scanner.scoring import classify_verdict, compute_score, compute_sub_scores, generate_reason
from range_scanner.state import assess_breakout_risk, classify_edge_position, compute_entry_quality, compute_position_in_range
from range_scanner.structure import detect_range_structure


_UNIVERSES_DIR = Path(__file__).parent.parent.parent.parent / "universes"


def _load_tickers(path: Path) -> list[str]:
    text = path.read_text()
    return [line.strip().upper() for line in text.splitlines() if line.strip() and not line.startswith("#")]


def _check_recent_validity(close: pd.Series, support: float, resistance: float) -> tuple[str, float]:
    latest = close.iloc[-1]
    if latest > resistance * 1.01:
        return "BROKEN_UP", 0.0
    if latest < support * 0.99:
        return "BROKEN_DOWN", 0.0
    recent = close.iloc[-20:]
    inside = ((recent >= support) & (recent <= resistance)).sum()
    recent_containment = inside / len(recent)
    if recent_containment < 0.60:
        return "STALE_RANGE", recent_containment
    return "ACTIVE", recent_containment


def _scan_single(ticker: str, config: ScannerConfig) -> TickerScanResult:
    """Scan one ticker — same logic as CLI but without context layer."""
    df = fetch_bars(ticker, config.lookback)
    if df is None or len(df) < config.min_candles:
        return TickerScanResult(ticker=ticker, verdict=Verdict.INSUFFICIENT_DATA,
                                skip_reason=f"Insufficient data ({len(df) if df is not None else 0} candles)")

    latest_close = df["close"].iloc[-1]
    if pd.isna(latest_close) or latest_close <= 0:
        return TickerScanResult(ticker=ticker, verdict=Verdict.ERROR, skip_reason="Invalid close price")

    avg_volume = df["volume"].iloc[-config.volume_avg_window:].mean()
    avg_dollar_volume = (df["close"].iloc[-config.volume_avg_window:] * df["volume"].iloc[-config.volume_avg_window:]).mean()

    if avg_volume < config.min_volume or avg_dollar_volume < config.min_dollar_volume:
        return TickerScanResult(ticker=ticker, verdict=Verdict.ILLIQUID,
                                skip_reason=f"Liquidity below threshold", latest_close=latest_close)

    adx_series = compute_adx(df["high"], df["low"], df["close"], config.adx_period)
    adx_val = float(adx_series.iloc[-1]) if pd.notna(adx_series.iloc[-1]) else 25.0
    atr_pct = compute_atr_pct(df["high"], df["low"], df["close"], config.atr_period)
    if atr_pct is None:
        return TickerScanResult(ticker=ticker, verdict=Verdict.ERROR, skip_reason="Cannot compute ATR")

    ema_slope = compute_ema_slope_pct(df["close"], config.ema_period, config.ema_slope_window) or 0.0
    gap_freq, avg_gap, _ = compute_gap_stats(df["open"], df["close"])
    comp_ratio, comp_label = compute_compression_ratio(df["high"], df["low"], df["close"])

    structure = detect_range_structure(df, config)
    if structure is None:
        return TickerScanResult(ticker=ticker, verdict=Verdict.MESSY_RANGE, score=20.0,
                                adx_14=round(adx_val, 2), atr_pct=round(atr_pct, 2),
                                latest_close=latest_close, skip_reason="No clear range structure")

    position = compute_position_in_range(latest_close, structure.support, structure.resistance)
    edge_pos = classify_edge_position(position)
    b_risk = assess_breakout_risk(df, position, structure.support, structure.resistance)
    entry_qual = compute_entry_quality(position, edge_pos, b_risk)

    validity_status, _ = _check_recent_validity(df["close"], structure.support, structure.resistance)
    breakdown = compute_score(structure, adx_val, atr_pct, ema_slope, avg_dollar_volume, config)

    score = breakdown.total
    if validity_status in ("BROKEN_UP", "BROKEN_DOWN"):
        score = min(score, 40.0)
    elif validity_status == "STALE_RANGE":
        score = min(score, 55.0)

    verdict = classify_verdict(score, adx_val, ema_slope, structure.trend_leakage,
                               structure.range_width_pct, structure.rotation_count,
                               edge_position=edge_pos, breakout_risk=b_risk)
    structure_score, regime_score, liquidity_sc = compute_sub_scores(breakdown)
    reason = generate_reason(structure, adx_val, ema_slope, verdict,
                             edge_position=edge_pos, entry_quality=entry_qual, breakout_risk=b_risk)

    if gap_freq > 0.15:
        reason += f"; frequent gaps ({gap_freq:.0%})"
    if comp_label != "NORMAL":
        reason += f"; volatility {comp_label.lower()}"

    return TickerScanResult(
        ticker=ticker, score=round(score, 2), verdict=verdict,
        entry_quality=entry_qual, position_in_range=round(position, 3),
        edge_position=edge_pos, breakout_risk=b_risk,
        support=structure.support, resistance=structure.resistance,
        range_width_pct=structure.range_width_pct,
        support_touches=structure.support_touches, resistance_touches=structure.resistance_touches,
        containment_ratio=structure.containment_ratio,
        adx_14=round(adx_val, 2), atr_pct=round(atr_pct, 2),
        ema20_slope_pct=round(ema_slope, 2),
        avg_volume_20=round(avg_volume, 0), avg_dollar_volume_20=round(avg_dollar_volume, 0),
        latest_close=latest_close, rotation_count=structure.rotation_count,
        tightness=structure.tightness, trend_leakage=structure.trend_leakage,
        gap_frequency=round(gap_freq, 4), avg_gap_pct=round(avg_gap, 2),
        compression_ratio=comp_ratio, compression_label=comp_label,
        structure_score=structure_score, regime_score=regime_score, liquidity_score=liquidity_sc,
        reason=reason,
    )


def render():
    st.title("Scanner")
    st.markdown("Run a scan on any universe and explore results interactively.")

    # Controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        universes = [f.stem for f in _UNIVERSES_DIR.glob("*.txt")]
        universe = st.selectbox("Universe", universes, index=0)

    with col2:
        lookback = st.number_input("Lookback (days)", min_value=30, max_value=252, value=120)

    with col3:
        min_dv = st.number_input("Min Dollar Volume ($M)", min_value=1, max_value=500, value=20)

    with col4:
        top_n = st.number_input("Show top N", min_value=5, max_value=100, value=20)

    # Custom tickers input
    custom_tickers = st.text_input("Or paste tickers (comma-separated)", placeholder="AAPL, MSFT, NVDA")

    if st.button("Run Scan", type="primary"):
        config = ScannerConfig(
            lookback=lookback,
            min_dollar_volume=min_dv * 1_000_000,
        )

        if custom_tickers.strip():
            ticker_list = [t.strip().upper() for t in custom_tickers.split(",") if t.strip()]
        else:
            ticker_path = _UNIVERSES_DIR / f"{universe}.txt"
            ticker_list = _load_tickers(ticker_path)

        progress = st.progress(0, text="Scanning...")
        results: list[TickerScanResult] = []

        for i, ticker in enumerate(ticker_list):
            progress.progress((i + 1) / len(ticker_list), text=f"Scanning {ticker}...")
            try:
                result = _scan_single(ticker, config)
            except Exception as e:
                result = TickerScanResult(ticker=ticker, verdict=Verdict.ERROR, skip_reason=str(e))
            results.append(result)

        progress.empty()

        # Store in session state
        st.session_state["scan_results"] = results
        st.session_state["scan_tickers"] = ticker_list

    # Display results
    if "scan_results" in st.session_state:
        results = st.session_state["scan_results"]
        passed = [r for r in results if r.skip_reason == ""]
        skipped = [r for r in results if r.skip_reason != ""]

        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Scanned", len(results))
        m2.metric("Passed", len(passed))
        m3.metric("Skipped", len(skipped))
        excellent = [r for r in passed if r.verdict == Verdict.EXCELLENT_RANGE]
        m4.metric("Excellent", len(excellent))

        st.markdown("---")

        # Results table
        ranked = sorted(passed, key=lambda r: r.score, reverse=True)[:top_n]

        if ranked:
            rows = []
            for r in ranked:
                rows.append({
                    "Ticker": r.ticker,
                    "Score": r.score,
                    "Entry": r.entry_quality or 0,
                    "Setup": r.setup_type.value.replace("_", " ") if r.setup_type else "—",
                    "Verdict": r.verdict.value.replace("_", " "),
                    "Edge": r.edge_position.value.replace("_", " ") if r.edge_position else "—",
                    "Risk": r.breakout_risk.value if r.breakout_risk else "—",
                    "Range": f"{r.support:.1f}–{r.resistance:.1f}" if r.support else "—",
                    "Width%": r.range_width_pct or 0,
                    "Rotations": r.rotation_count or 0,
                    "Gaps%": round((r.gap_frequency or 0) * 100, 1),
                    "Reason": r.reason[:80] if r.reason else "",
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, height=600)

        # Skipped tickers expander
        if skipped:
            with st.expander(f"Skipped tickers ({len(skipped)})"):
                skip_rows = [{"Ticker": r.ticker, "Verdict": r.verdict.value, "Reason": r.skip_reason} for r in skipped]
                st.dataframe(pd.DataFrame(skip_rows), use_container_width=True)
