"""
Scanner Page — The main workhorse. Pick a universe, run a scan, explore results.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from range_scanner.config import ScannerConfig
from range_scanner.data import fetch_bars, fetch_bars_batch
from range_scanner.indicators import (
    compute_adx, compute_atr_pct, compute_compression_ratio,
    compute_ema_slope_pct, compute_gap_stats,
)
from range_scanner.models import TickerScanResult, Verdict, EdgePosition, BreakoutRisk
from range_scanner.scoring import classify_verdict, compute_score, compute_sub_scores, generate_reason
from range_scanner.state import assess_breakout_risk, classify_edge_position, compute_entry_quality, compute_position_in_range
from range_scanner.structure import detect_range_structure


_UNIVERSES_DIR = Path.cwd() / "universes"


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


def _verdict_color(verdict: str) -> str:
    colors = {
        "EXCELLENT RANGE": "#5B8A72",
        "RANGE PRESSING RESISTANCE": "#C27D5E",
        "RANGE PRESSING SUPPORT": "#5B8A72",
        "WATCHLIST": "#B8860B",
        "BROKEN UP": "#C0392B",
        "BROKEN DOWN": "#C0392B",
        "TRENDING NOT RANGE": "#7A756E",
        "MESSY RANGE": "#B8B2A8",
        "TOO WIDE": "#C0392B",
        "WIDE RANGE": "#C27D5E",
    }
    return colors.get(verdict, "#7A756E")


def render():
    st.title("Scanner")
    st.markdown('<p class="subtitle">Scan any universe for range-bound candidates. Results ranked by structure quality.</p>', unsafe_allow_html=True)

    # Help expander
    with st.expander("How to use this page", expanded=False):
        st.markdown("""
        **1. Choose your universe** — Pick from built-in lists (Nasdaq-100, ETFs) or paste your own tickers.

        **2. Set filters** — Lookback controls how many days of history to analyze.
        Min Dollar Volume filters out illiquid stocks that are hard to trade.

        **3. Click "Run Scan"** — The scanner will fetch data and analyze each ticker.
        This takes ~1-2 seconds per ticker.

        **4. Read the results:**
        - **Score** (0-100) = How clean is the range structure?
        - **Entry** (0-100) = Is price at a useful edge right now?
        - **Verdict** = What type of setup is this?
        - **Reason** = Human-readable explanation of why

        **What the verdicts mean:**
        - 🟢 **EXCELLENT RANGE** — Clean rotational structure, actively trading in range
        - 🔵 **PRESSING SUPPORT/RESISTANCE** — Valid range, price is near an edge
        - 🟡 **WATCHLIST** — Decent range but not at an actionable edge
        - 🔴 **BROKEN UP/DOWN** — Price has exited the range
        - ⚫ **TRENDING** — Not range-bound, strong directional movement
        """)

    st.markdown("---")

    # Controls row
    st.markdown("### Scan Configuration")

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        universes = sorted([f.stem for f in _UNIVERSES_DIR.glob("*.txt")])
        universe = st.selectbox(
            "Universe",
            universes,
            index=universes.index("nasdaq100") if "nasdaq100" in universes else 0,
            help="Pre-built stock lists. Nasdaq-100 is ~90 large tech/growth stocks. ETFs includes sector and commodity funds.",
        )

    with col2:
        lookback = st.number_input(
            "Lookback (days)",
            min_value=30, max_value=252, value=120, step=10,
            help="How many trading days of history to analyze. 120 = ~6 months. Shorter = more recent ranges only.",
        )

    with col3:
        min_dv = st.number_input(
            "Min $ Volume (M)",
            min_value=1, max_value=500, value=20, step=5,
            help="Minimum average daily dollar volume in millions. Filters out stocks too illiquid to trade comfortably.",
        )

    with col4:
        top_n = st.number_input(
            "Show top N",
            min_value=5, max_value=100, value=20, step=5,
            help="Number of top results to display in the table.",
        )

    # Custom tickers
    custom_tickers = st.text_input(
        "Or paste custom tickers (comma-separated)",
        placeholder="AAPL, MSFT, NVDA, TSLA, GME",
        help="Override the universe with your own list. Separate with commas.",
    )

    # Scan button
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        run_scan = st.button("Run Scan", type="primary", use_container_width=True)
    with col_info:
        if custom_tickers.strip():
            count = len([t for t in custom_tickers.split(",") if t.strip()])
            st.markdown(f"<span style='color: #7A756E; font-size: 0.85rem;'>Will scan {count} custom tickers</span>", unsafe_allow_html=True)
        else:
            ticker_path = _UNIVERSES_DIR / f"{universe}.txt"
            if ticker_path.exists():
                count = len(_load_tickers(ticker_path))
                st.markdown(f"<span style='color: #7A756E; font-size: 0.85rem;'>Will scan {count} tickers from {universe}</span>", unsafe_allow_html=True)

    if run_scan:
        config = ScannerConfig(
            lookback=lookback,
            min_dollar_volume=min_dv * 1_000_000,
        )

        if custom_tickers.strip():
            ticker_list = [t.strip().upper() for t in custom_tickers.split(",") if t.strip()]
        else:
            ticker_path = _UNIVERSES_DIR / f"{universe}.txt"
            ticker_list = _load_tickers(ticker_path)

        # Phase 1: Fetch all data concurrently (the slow part)
        progress = st.progress(0, text="Fetching market data (parallel)...")
        all_data = fetch_bars_batch(ticker_list, lookback, max_workers=10)
        progress.progress(0.7, text="Analyzing structures...")

        # Phase 2: Analyze each ticker (fast, CPU-only)
        results: list[TickerScanResult] = []
        for i, ticker in enumerate(ticker_list):
            progress.progress(0.7 + 0.3 * (i + 1) / len(ticker_list), text=f"Analyzing {ticker}...")
            try:
                result = _scan_single(ticker, config)
            except Exception as e:
                result = TickerScanResult(ticker=ticker, verdict=Verdict.ERROR, skip_reason=str(e))
            results.append(result)

        progress.empty()
        st.session_state["scan_results"] = results
        # Rule 46: timestamp on all market data
        from datetime import datetime
        st.session_state["scan_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Display results
    if "scan_results" in st.session_state:
        results = st.session_state["scan_results"]
        passed = [r for r in results if r.skip_reason == ""]
        skipped = [r for r in results if r.skip_reason != ""]

        st.markdown("---")

        # Rule 46: Show when data was fetched
        ts = st.session_state.get("scan_timestamp", "")
        st.markdown(f'<p style="color: #B8B2A8; font-size: 0.75rem; font-family: \'JetBrains Mono\', monospace;">Last scanned: {ts}</p>', unsafe_allow_html=True)

        st.markdown("### Results Overview")

        # Summary metrics
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Scanned", len(results))
        m2.metric("Passed Filters", len(passed))
        m3.metric("Skipped", len(skipped))
        excellent = [r for r in passed if "EXCELLENT" in r.verdict.value]
        m4.metric("Excellent", len(excellent))
        actionable = [r for r in passed if r.entry_quality and r.entry_quality >= 60]
        m5.metric("Actionable (Entry≥60)", len(actionable))

        st.markdown("---")

        # Results tabs
        tab1, tab2, tab3 = st.tabs(["📋 Ranked Results", "🎯 Actionable Only", "⊘ Skipped"])

        with tab1:
            ranked = sorted(passed, key=lambda r: r.score, reverse=True)[:top_n]
            if ranked:
                _render_results_table(ranked)
                _render_narratives(ranked[:10])
            else:
                st.info("No range candidates found. Try a different universe or lower the filters.")

        with tab2:
            actionable_results = sorted(
                [r for r in passed if r.entry_quality and r.entry_quality >= 50 and r.score >= 55],
                key=lambda r: r.entry_quality or 0, reverse=True
            )
            if actionable_results:
                st.markdown("*Filtered to tickers with Entry Quality ≥ 50 and Range Score ≥ 55*")
                _render_results_table(actionable_results[:top_n])
            else:
                st.info("No actionable setups found right now. Price may be mid-range for most candidates.")

        with tab3:
            if skipped:
                skip_rows = []
                for r in skipped:
                    skip_rows.append({
                        "Ticker": r.ticker,
                        "Verdict": r.verdict.value.replace("_", " "),
                        "Reason": r.skip_reason,
                    })
                st.dataframe(pd.DataFrame(skip_rows), use_container_width=True, hide_index=True)
            else:
                st.success("No tickers were skipped!")


def _render_results_table(results: list[TickerScanResult]):
    """Render a rich results table with color coding."""
    rows = []
    for r in results:
        verdict_display = r.verdict.value.replace("_", " ")
        edge_display = r.edge_position.value.replace("_", " ") if r.edge_position else "—"

        rows.append({
            "Ticker": r.ticker,
            "Score": r.score,
            "Entry": r.entry_quality or 0,
            "Verdict": verdict_display,
            "Edge": edge_display,
            "Risk": r.breakout_risk.value if r.breakout_risk else "—",
            "Range": f"${r.support:.1f} – ${r.resistance:.1f}" if r.support else "—",
            "Width%": r.range_width_pct or 0,
            "Rot.": r.rotation_count or 0,
            "Gaps%": round((r.gap_frequency or 0) * 100, 1),
            "Price": f"${r.latest_close:.2f}" if r.latest_close else "—",
            "Reason": (r.reason or "")[:100],
        })

    df = pd.DataFrame(rows)

    # Style the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        height=min(600, 50 + len(rows) * 35),
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
            "Entry": st.column_config.ProgressColumn("Entry", min_value=0, max_value=100, format="%d"),
            "Width%": st.column_config.NumberColumn("Width%", format="%.1f"),
            "Rot.": st.column_config.NumberColumn("Rot.", format="%d"),
            "Gaps%": st.column_config.NumberColumn("Gaps%", format="%.1f"),
            "Reason": st.column_config.TextColumn("Reason", width="large"),
        },
    )

    # Legend
    st.markdown("""
    <div style="font-size: 0.75rem; color: #7A756E; margin-top: 8px; padding: 12px; background: #F5F2EE; border-radius: 8px;">
        <strong>Score</strong> = Range structure quality (rotations, containment, width) &nbsp;|&nbsp;
        <strong>Entry</strong> = How close to an edge with low breakout risk &nbsp;|&nbsp;
        <strong>Rot.</strong> = Number of full rotations between zones &nbsp;|&nbsp;
        <strong>Gaps%</strong> = Frequency of >2% overnight gaps (lower = better for range trading)
    </div>
    """, unsafe_allow_html=True)


def _render_narratives(results: list[TickerScanResult]):
    """Show AI-style narrative analysis for top results."""
    from range_scanner.reasoning import generate_narrative

    st.markdown("")
    with st.expander("📝 Detailed Analysis (top 10)", expanded=False):
        for r in results:
            if r.skip_reason:
                continue
            narrative = generate_narrative(r)
            verdict_display = r.verdict.value.replace("_", " ")

            st.markdown(f"""
            <div style="background: #F5F2EE; border-left: 3px solid #5B8A72; padding: 16px 20px;
                        border-radius: 0 8px 8px 0; margin: 12px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 600; font-size: 1rem; color: #2D2A26;">{r.ticker}</span>
                    <span style="font-size: 0.8rem; color: #7A756E;">{verdict_display} · Score {r.score:.0f} · Entry {r.entry_quality:.0f if r.entry_quality else 0}</span>
                </div>
                <p style="margin: 0; line-height: 1.7; color: #4A4540; font-size: 0.9rem;">{narrative}</p>
            </div>
            """, unsafe_allow_html=True)
