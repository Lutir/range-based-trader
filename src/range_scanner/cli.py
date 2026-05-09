from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from range_scanner.config import ScannerConfig
from range_scanner.data import fetch_bars
from range_scanner.indicators import compute_adx, compute_atr_pct, compute_ema_slope_pct
from range_scanner.models import BreakoutRisk, EdgePosition, TickerScanResult, Verdict
from range_scanner.output import console, print_summary, write_csv
from range_scanner.scoring import classify_verdict, compute_score, compute_sub_scores, generate_reason
from range_scanner.state import assess_breakout_risk, classify_edge_position, compute_entry_quality, compute_position_in_range
from range_scanner.structure import detect_range_structure

app = typer.Typer(help="Range Candidate Scanner")


def _load_tickers(path: Path) -> list[str]:
    text = path.read_text()
    tickers = [line.strip().upper() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    return tickers


def _compute_risk_note(close: pd.Series, support: float, resistance: float) -> str:
    midpoint = (support + resistance) / 2
    recent = close.iloc[-10:]
    above_mid = (recent > midpoint).sum()
    if above_mid >= 8:
        return "HIGH_UPSIDE_BREAKOUT_RISK"
    if above_mid <= 2:
        return "HIGH_DOWNSIDE_BREAKDOWN_RISK"
    return ""


def _check_recent_validity(close: pd.Series, support: float, resistance: float) -> tuple[str, float]:
    """Check if range is still valid based on last 20 candles.
    Returns (status, recent_containment_ratio)."""
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


def _extract_dates(df: pd.DataFrame) -> tuple[str, str]:
    start = str(df["timestamp"].iloc[0])[:10]
    end = str(df["timestamp"].iloc[-1])[:10]
    return start, end


def _scan_ticker(ticker: str, config: ScannerConfig) -> tuple[TickerScanResult, pd.DataFrame | None]:
    """Returns (result, dataframe) — dataframe kept for chart export."""
    df = fetch_bars(ticker, config.lookback)
    if df is None or len(df) < config.min_candles:
        return TickerScanResult(
            ticker=ticker, verdict=Verdict.INSUFFICIENT_DATA,
            skip_reason=f"Insufficient data ({len(df) if df is not None else 0} candles)",
        ), None

    data_start, data_end = _extract_dates(df)

    latest_close = df["close"].iloc[-1]
    if pd.isna(latest_close) or latest_close <= 0:
        return TickerScanResult(
            ticker=ticker, verdict=Verdict.ERROR,
            skip_reason="Invalid latest close price",
            data_start=data_start, data_end=data_end,
        ), None

    avg_volume = df["volume"].iloc[-config.volume_avg_window:].mean()
    avg_dollar_volume = (df["close"].iloc[-config.volume_avg_window:] * df["volume"].iloc[-config.volume_avg_window:]).mean()

    if avg_volume < config.min_volume or avg_dollar_volume < config.min_dollar_volume:
        return TickerScanResult(
            ticker=ticker, verdict=Verdict.ILLIQUID,
            skip_reason=f"Liquidity below threshold (vol={avg_volume:.0f}, dv={avg_dollar_volume:.0f})",
            latest_close=latest_close,
            avg_volume_20=round(avg_volume, 0),
            avg_dollar_volume_20=round(avg_dollar_volume, 0),
            data_start=data_start, data_end=data_end,
        ), None

    adx_series = compute_adx(df["high"], df["low"], df["close"], config.adx_period)
    adx_val = adx_series.iloc[-1]
    if pd.isna(adx_val):
        adx_val = 25.0

    atr_pct = compute_atr_pct(df["high"], df["low"], df["close"], config.atr_period)
    if atr_pct is None:
        return TickerScanResult(
            ticker=ticker, verdict=Verdict.ERROR,
            skip_reason="Cannot compute ATR",
        ), None

    ema_slope = compute_ema_slope_pct(df["close"], config.ema_period, config.ema_slope_window)
    if ema_slope is None:
        ema_slope = 0.0

    structure = detect_range_structure(df, config)
    if structure is None:
        return TickerScanResult(
            ticker=ticker, verdict=Verdict.MESSY_RANGE, score=20.0,
            adx_14=round(adx_val, 2), atr_pct=round(atr_pct, 2),
            ema20_slope_pct=round(ema_slope, 2), latest_close=latest_close,
            avg_volume_20=round(avg_volume, 0), avg_dollar_volume_20=round(avg_dollar_volume, 0),
            data_start=data_start, data_end=data_end,
            skip_reason="No clear range structure detected",
        ), df

    # Edge position and state classification
    position = compute_position_in_range(latest_close, structure.support, structure.resistance)
    edge_pos = classify_edge_position(position)
    b_risk = assess_breakout_risk(df, position, structure.support, structure.resistance)
    entry_qual = compute_entry_quality(position, edge_pos, b_risk)

    # Recent validity check
    validity_status, recent_containment = _check_recent_validity(
        df["close"], structure.support, structure.resistance
    )

    breakdown = compute_score(structure, adx_val, atr_pct, ema_slope, avg_dollar_volume, config)

    # Downgrade score if range is no longer active
    score = breakdown.total
    if validity_status == "BROKEN_UP" or validity_status == "BROKEN_DOWN":
        score = min(score, 40.0)
    elif validity_status == "STALE_RANGE":
        score = min(score, 55.0)

    verdict = classify_verdict(
        score, adx_val, ema_slope,
        structure.trend_leakage, structure.range_width_pct, structure.rotation_count,
        edge_position=edge_pos, breakout_risk=b_risk,
    )
    risk_note = _compute_risk_note(df["close"], structure.support, structure.resistance)
    structure_score, regime_score, liquidity_sc = compute_sub_scores(breakdown)
    reason = generate_reason(
        structure, adx_val, ema_slope, verdict,
        edge_position=edge_pos, entry_quality=entry_qual, breakout_risk=b_risk,
    )

    # Append validity note if stale
    if validity_status == "STALE_RANGE" and edge_pos not in (EdgePosition.BROKEN_UP, EdgePosition.BROKEN_DOWN):
        reason += f"; stale (recent containment {recent_containment:.0%})"

    return TickerScanResult(
        ticker=ticker,
        score=round(score, 2),
        verdict=verdict,
        entry_quality=entry_qual,
        position_in_range=round(position, 3),
        edge_position=edge_pos,
        breakout_risk=b_risk,
        support=structure.support,
        resistance=structure.resistance,
        range_width_pct=structure.range_width_pct,
        support_touches=structure.support_touches,
        resistance_touches=structure.resistance_touches,
        containment_ratio=structure.containment_ratio,
        adx_14=round(adx_val, 2),
        atr_pct=round(atr_pct, 2),
        ema20_slope_pct=round(ema_slope, 2),
        avg_volume_20=round(avg_volume, 0),
        avg_dollar_volume_20=round(avg_dollar_volume, 0),
        latest_close=latest_close,
        rotation_count=structure.rotation_count,
        tightness=structure.tightness,
        trend_leakage=structure.trend_leakage,
        structure_score=structure_score,
        regime_score=regime_score,
        liquidity_score=liquidity_sc,
        data_start=data_start,
        data_end=data_end,
        risk_note=risk_note,
        reason=reason,
    ), df


_UNIVERSES_DIR = Path(__file__).parent.parent.parent / "universes"

_UNIVERSE_MAP = {
    "personal": "personal.txt",
    "nasdaq100": "nasdaq100.txt",
    "sp500": "sp500.txt",
    "etfs": "etfs.txt",
    "russell1000": "russell1000.txt",
}


def _resolve_tickers(tickers: Path, universe: str | None) -> Path:
    if universe:
        filename = _UNIVERSE_MAP.get(universe)
        if not filename:
            console.print(f"[red]Unknown universe: {universe}. Available: {', '.join(_UNIVERSE_MAP.keys())}[/red]")
            raise typer.Exit(1)
        path = _UNIVERSES_DIR / filename
        if not path.exists():
            console.print(f"[red]Universe file not found: {path}[/red]")
            raise typer.Exit(1)
        return path
    return tickers


@app.command()
def scan(
    tickers: Annotated[Path, typer.Option(help="Path to ticker file")] = Path("tickers.txt"),
    universe: Annotated[str | None, typer.Option(help="Built-in universe: personal, nasdaq100, sp500, etfs")] = None,
    lookback: Annotated[int, typer.Option(help="Number of daily candles")] = 120,
    output: Annotated[Path, typer.Option(help="CSV output path")] = Path("results.csv"),
    min_volume: Annotated[int, typer.Option(help="Minimum average daily volume")] = 1_000_000,
    min_dollar_volume: Annotated[int, typer.Option(help="Minimum average dollar volume")] = 20_000_000,
    top: Annotated[int, typer.Option(help="Top results to display")] = 20,
    charts: Annotated[bool, typer.Option(help="Export PNG charts for top candidates")] = False,
    charts_dir: Annotated[Path, typer.Option(help="Directory for chart PNGs")] = Path("charts"),
    context: Annotated[bool, typer.Option(help="Add market/sector context layer")] = False,
) -> None:
    """Scan tickers for range-bound structure."""
    tickers = _resolve_tickers(tickers, universe)

    config = ScannerConfig(
        lookback=lookback,
        min_volume=min_volume,
        min_dollar_volume=min_dollar_volume,
        top=top,
    )

    # Fetch market context if requested
    market_regime = None
    market_details: dict = {}
    sector_cache: dict[str, tuple] = {}
    spy_df: pd.DataFrame | None = None

    if context:
        from range_scanner.context import (
            MarketRegime, fetch_market_regime, fetch_sector_regime,
            get_sector_etf, compute_relative_strength, fetch_bars,
        )
        console.print("[dim]Fetching market context...[/dim]")
        market_regime, market_details = fetch_market_regime(lookback)
        regime_label = market_regime.value.replace("_", " ")
        console.print(f"[bold]Market regime:[/bold] {regime_label}")
        if market_details:
            console.print(f"[dim]  SPY ADX={market_details.get('spy_adx')} slope={market_details.get('spy_slope')}% | QQQ ADX={market_details.get('qqq_adx')} slope={market_details.get('qqq_slope')}%[/dim]")
        spy_df = fetch_bars("SPY", lookback)

    ticker_list = _load_tickers(tickers)
    if not ticker_list:
        console.print("[red]No tickers found in file.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Scanning {len(ticker_list)} tickers...[/bold]")
    results: list[TickerScanResult] = []
    dataframes: dict[str, pd.DataFrame] = {}

    for ticker in ticker_list:
        try:
            result, df = _scan_ticker(ticker, config)

            # Enrich with context if available
            if context and df is not None and result.skip_reason == "":
                from range_scanner.context import (
                    get_sector_etf, fetch_sector_regime, compute_relative_strength,
                    SectorRegime,
                )
                sector_etf = get_sector_etf(ticker)

                # Cache sector lookups
                if sector_etf not in sector_cache:
                    sector_cache[sector_etf] = fetch_sector_regime(sector_etf, lookback)
                sec_regime, sec_slope = sector_cache[sector_etf]

                # Relative strength vs SPY
                rs_20 = 0.0
                if spy_df is not None:
                    rs_20 = compute_relative_strength(df, spy_df, 20)

                # Append context to reason
                ctx_parts = []
                ctx_parts.append(f"market {market_regime.value.replace('_', ' ').lower()}")
                ctx_parts.append(f"sector ({sector_etf}) {sec_regime.value.replace('_', ' ').lower()}")
                if rs_20 > 3:
                    ctx_parts.append(f"RS +{rs_20:.1f}% (outperforming)")
                elif rs_20 < -3:
                    ctx_parts.append(f"RS {rs_20:.1f}% (underperforming)")

                result.reason += "; " + "; ".join(ctx_parts)

        except Exception as e:
            result = TickerScanResult(
                ticker=ticker, verdict=Verdict.ERROR,
                skip_reason=f"Exception: {e}",
            )
            df = None
        results.append(result)
        if df is not None:
            dataframes[ticker] = df

    write_csv(results, output)
    print_summary(results, top, len(ticker_list))
    console.print(f"\n[green]Results written to {output}[/green]")

    if charts:
        from range_scanner.charts import export_chart

        passed = [r for r in results if r.skip_reason == "" and r.ticker in dataframes]
        ranked = sorted(passed, key=lambda r: r.score, reverse=True)[:top]

        if not ranked:
            console.print("[yellow]No charts to export.[/yellow]")
            return

        console.print(f"\n[bold]Exporting {len(ranked)} charts to {charts_dir}/[/bold]")
        for i, r in enumerate(ranked, 1):
            filepath = export_chart(dataframes[r.ticker], r, i, charts_dir)
            console.print(f"  {filepath.name}")
        console.print(f"[green]Charts exported to {charts_dir}/[/green]")
