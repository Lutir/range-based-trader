"""Market context layer: regime, sector, relative strength, earnings."""

from enum import Enum

import pandas as pd
import requests

from range_scanner.data import fetch_bars, _get_headers, _get_base_url


class MarketRegime(str, Enum):
    CALM_RANGE_FRIENDLY = "CALM_RANGE_FRIENDLY"
    RISK_ON_TRENDING = "RISK_ON_TRENDING"
    RISK_OFF_VOLATILE = "RISK_OFF_VOLATILE"
    MIXED = "MIXED"


class SectorRegime(str, Enum):
    STABLE = "STABLE"
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    VOLATILE = "VOLATILE"


SECTOR_MAP: dict[str, str] = {
    # Technology
    "AAPL": "XLK", "MSFT": "XLK", "ADBE": "XLK", "CRM": "XLK", "INTU": "XLK",
    "ADSK": "XLK", "SNPS": "XLK", "CDNS": "XLK", "FTNT": "XLK", "PANW": "XLK",
    "CRWD": "XLK", "ZS": "XLK", "DDOG": "XLK", "TEAM": "XLK", "WDAY": "XLK",
    "ROP": "XLK", "ANSS": "XLK", "TTD": "XLK", "MDB": "XLK",
    # Semiconductors
    "NVDA": "SMH", "AMD": "SMH", "AVGO": "SMH", "QCOM": "SMH", "TXN": "SMH",
    "AMAT": "SMH", "LRCX": "SMH", "KLAC": "SMH", "ADI": "SMH", "NXPI": "SMH",
    "MRVL": "SMH", "MCHP": "SMH", "ON": "SMH", "MU": "SMH", "INTC": "SMH",
    "ARM": "SMH", "GFS": "SMH", "TSM": "SMH",
    # Communication/Internet
    "META": "XLC", "GOOGL": "XLC", "GOOG": "XLC", "NFLX": "XLC", "TMUS": "XLC",
    "CHTR": "XLC", "EA": "XLC", "WBD": "XLC",
    # Consumer Discretionary
    "AMZN": "XLY", "TSLA": "XLY", "COST": "XLY", "BKNG": "XLY", "SBUX": "XLY",
    "ORLY": "XLY", "ROST": "XLY", "ABNB": "XLY", "LULU": "XLY", "MAR": "XLY",
    "PCAR": "XLY", "ODFL": "XLY", "CSX": "XLY", "DASH": "XLY",
    # Consumer Staples
    "PEP": "XLP", "MDLZ": "XLP", "KDP": "XLP", "MNST": "XLP", "KHC": "XLP",
    "CCEP": "XLP",
    # Healthcare
    "AMGN": "XLV", "GILD": "XLV", "ISRG": "XLV", "VRTX": "XLV", "REGN": "XLV",
    "DXCM": "XLV", "IDXX": "XLV", "ILMN": "XLV", "BIIB": "XLV", "GEHC": "XLV",
    "TMO": "XLV", "ABT": "XLV", "JNJ": "XLV", "UNH": "XLV", "MRK": "XLV",
    # Industrials
    "HON": "XLI", "CTAS": "XLI", "PAYX": "XLI", "FAST": "XLI", "VRSK": "XLI",
    "CDW": "XLI", "GE": "XLI", "LIN": "XLI",
    # Financials
    "JPM": "XLF", "V": "XLF", "MA": "XLF", "PYPL": "XLF", "ADP": "XLF",
    "SOFI": "XLF",
    # Utilities
    "AEP": "XLU", "XEL": "XLU", "EXC": "XLU", "CEG": "XLU",
    # Energy
    "BKR": "XLE",
    # Speculative/Other
    "GME": "XLY", "RKLB": "XLI", "APLD": "XLK", "BBAI": "XLK",
    "RGTI": "XLK", "LAES": "XLK", "ALB": "XLB", "ETOR": "XLF",
    "NKE": "XLY", "DIS": "XLY", "HD": "XLY", "WMT": "XLP", "PG": "XLP",
    "KO": "XLP",
}


def _compute_adx_value(df: pd.DataFrame) -> float:
    from range_scanner.indicators import compute_adx
    adx = compute_adx(df["high"], df["low"], df["close"], period=14)
    val = adx.iloc[-1]
    return float(val) if pd.notna(val) else 25.0


def _compute_ema_slope(df: pd.DataFrame, period: int = 20) -> float:
    from range_scanner.indicators import compute_ema_slope_pct
    slope = compute_ema_slope_pct(df["close"], period=period, slope_window=period)
    return slope if slope is not None else 0.0


def _compute_return(df: pd.DataFrame, days: int) -> float:
    if len(df) < days:
        return 0.0
    start = df["close"].iloc[-days]
    end = df["close"].iloc[-1]
    if start <= 0:
        return 0.0
    return (end - start) / start * 100


def fetch_market_regime(lookback: int = 60) -> tuple[MarketRegime, dict]:
    """Assess market regime using SPY, QQQ, and VIX."""
    spy_df = fetch_bars("SPY", lookback)
    qqq_df = fetch_bars("QQQ", lookback)
    # VIX is not available as a stock on Alpaca — use VIXY as proxy or skip
    # For MVP, use SPY/QQQ trend indicators only

    if spy_df is None or qqq_df is None:
        return MarketRegime.MIXED, {}

    spy_adx = _compute_adx_value(spy_df)
    qqq_adx = _compute_adx_value(qqq_df)
    spy_slope = _compute_ema_slope(spy_df)
    qqq_slope = _compute_ema_slope(qqq_df)
    spy_atr_pct = _compute_atr_pct_simple(spy_df)
    qqq_atr_pct = _compute_atr_pct_simple(qqq_df)

    details = {
        "spy_adx": round(spy_adx, 1),
        "qqq_adx": round(qqq_adx, 1),
        "spy_slope": round(spy_slope, 2),
        "qqq_slope": round(qqq_slope, 2),
        "spy_atr_pct": round(spy_atr_pct, 2),
        "qqq_atr_pct": round(qqq_atr_pct, 2),
    }

    avg_adx = (spy_adx + qqq_adx) / 2
    avg_slope = (abs(spy_slope) + abs(qqq_slope)) / 2
    avg_atr = (spy_atr_pct + qqq_atr_pct) / 2

    # High ATR + high ADX = risk-off volatile
    if avg_atr > 2.0 and avg_adx > 25:
        return MarketRegime.RISK_OFF_VOLATILE, details
    # Strong trend = risk-on trending
    if avg_adx > 25 and avg_slope > 3:
        return MarketRegime.RISK_ON_TRENDING, details
    # Low ADX + low slope = calm
    if avg_adx < 22 and avg_slope < 3:
        return MarketRegime.CALM_RANGE_FRIENDLY, details

    return MarketRegime.MIXED, details


def _compute_atr_pct_simple(df: pd.DataFrame) -> float:
    from range_scanner.indicators import compute_atr
    atr = compute_atr(df["high"], df["low"], df["close"], period=14)
    latest_atr = atr.iloc[-1]
    latest_close = df["close"].iloc[-1]
    if pd.isna(latest_atr) or latest_close <= 0:
        return 0.0
    return latest_atr / latest_close * 100


def fetch_sector_regime(sector_etf: str, lookback: int = 60) -> tuple[SectorRegime, float]:
    """Assess sector regime and return (regime, ema_slope)."""
    df = fetch_bars(sector_etf, lookback)
    if df is None or len(df) < 30:
        return SectorRegime.STABLE, 0.0

    adx = _compute_adx_value(df)
    slope = _compute_ema_slope(df)
    atr_pct = _compute_atr_pct_simple(df)

    if atr_pct > 2.5:
        return SectorRegime.VOLATILE, slope
    if adx > 25 and slope > 3:
        return SectorRegime.TRENDING_UP, slope
    if adx > 25 and slope < -3:
        return SectorRegime.TRENDING_DOWN, slope
    return SectorRegime.STABLE, slope


def compute_relative_strength(stock_df: pd.DataFrame, benchmark_df: pd.DataFrame, days: int = 20) -> float:
    """Returns stock return - benchmark return over N days."""
    stock_ret = _compute_return(stock_df, days)
    bench_ret = _compute_return(benchmark_df, days)
    return round(stock_ret - bench_ret, 2)


def fetch_days_to_earnings(ticker: str) -> int | None:
    """Fetch days until next earnings from Alpaca calendar endpoint.
    Returns None if unavailable."""
    try:
        from datetime import datetime, timedelta
        base_url = _get_base_url().replace("data.", "paper-api.")
        # Alpaca doesn't have a free earnings endpoint in market data API
        # For MVP, return None and note this needs an external source
        return None
    except Exception:
        return None


def get_sector_etf(ticker: str) -> str:
    """Map ticker to sector ETF. Defaults to SPY if unknown."""
    return SECTOR_MAP.get(ticker, "SPY")
