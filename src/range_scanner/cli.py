from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from range_scanner.config import ScannerConfig
from range_scanner.data import fetch_bars
from range_scanner.indicators import compute_adx, compute_atr_pct, compute_ema_slope_pct
from range_scanner.models import TickerScanResult, Verdict
from range_scanner.output import console, print_summary, write_csv
from range_scanner.scoring import classify_verdict, compute_score, compute_sub_scores, generate_reason
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


def _extract_dates(df: pd.DataFrame) -> tuple[str, str]:
    start = str(df["timestamp"].iloc[0])[:10]
    end = str(df["timestamp"].iloc[-1])[:10]
    return start, end


def _scan_ticker(ticker: str, config: ScannerConfig) -> TickerScanResult:
    df = fetch_bars(ticker, config.lookback)
    if df is None or len(df) < config.min_candles:
        return TickerScanResult(
            ticker=ticker, verdict=Verdict.INSUFFICIENT_DATA,
            skip_reason=f"Insufficient data ({len(df) if df is not None else 0} candles)",
        )

    data_start, data_end = _extract_dates(df)

    latest_close = df["close"].iloc[-1]
    if pd.isna(latest_close) or latest_close <= 0:
        return TickerScanResult(
            ticker=ticker, verdict=Verdict.ERROR,
            skip_reason="Invalid latest close price",
            data_start=data_start, data_end=data_end,
        )

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
        )

    adx_series = compute_adx(df["high"], df["low"], df["close"], config.adx_period)
    adx_val = adx_series.iloc[-1]
    if pd.isna(adx_val):
        adx_val = 25.0

    atr_pct = compute_atr_pct(df["high"], df["low"], df["close"], config.atr_period)
    if atr_pct is None:
        return TickerScanResult(
            ticker=ticker, verdict=Verdict.ERROR,
            skip_reason="Cannot compute ATR",
        )

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
        )

    breakdown = compute_score(structure, adx_val, atr_pct, ema_slope, avg_dollar_volume, config)
    verdict = classify_verdict(
        breakdown.total, adx_val, ema_slope,
        structure.trend_leakage, structure.range_width_pct, structure.rotation_count,
    )
    risk_note = _compute_risk_note(df["close"], structure.support, structure.resistance)
    structure_score, regime_score, liquidity_sc = compute_sub_scores(breakdown)
    reason = generate_reason(structure, adx_val, ema_slope, verdict)

    return TickerScanResult(
        ticker=ticker,
        score=breakdown.total,
        verdict=verdict,
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
    )


@app.command()
def scan(
    tickers: Annotated[Path, typer.Option(help="Path to ticker file")] = Path("tickers.txt"),
    lookback: Annotated[int, typer.Option(help="Number of daily candles")] = 120,
    output: Annotated[Path, typer.Option(help="CSV output path")] = Path("results.csv"),
    min_volume: Annotated[int, typer.Option(help="Minimum average daily volume")] = 1_000_000,
    min_dollar_volume: Annotated[int, typer.Option(help="Minimum average dollar volume")] = 20_000_000,
    top: Annotated[int, typer.Option(help="Top results to display")] = 20,
) -> None:
    """Scan tickers for range-bound structure."""
    config = ScannerConfig(
        lookback=lookback,
        min_volume=min_volume,
        min_dollar_volume=min_dollar_volume,
        top=top,
    )

    ticker_list = _load_tickers(tickers)
    if not ticker_list:
        console.print("[red]No tickers found in file.[/red]")
        raise typer.Exit(1)

    console.print(f"[bold]Scanning {len(ticker_list)} tickers...[/bold]")
    results: list[TickerScanResult] = []

    for ticker in ticker_list:
        try:
            result = _scan_ticker(ticker, config)
        except Exception as e:
            result = TickerScanResult(
                ticker=ticker, verdict=Verdict.ERROR,
                skip_reason=f"Exception: {e}",
            )
        results.append(result)

    write_csv(results, output)
    print_summary(results, top, len(ticker_list))
    console.print(f"\n[green]Results written to {output}[/green]")
