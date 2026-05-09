"""
Technical indicators for range detection.

These are the mathematical building blocks that measure:
- How volatile a stock is (ATR)
- Whether it's trending or sideways (ADX)
- What direction it's drifting (EMA slope)
- Whether volatility is coiling or expanding (compression)
- How often price gaps overnight (gap stats)

EXAMPLE: Imagine a stock trading between $100-$110 for months.
- ATR tells you the average daily movement (e.g., $2/day = 2%)
- ADX tells you if it's trending (low ADX = sideways = good for ranges)
- EMA slope tells you if there's a slow drift up or down
- Compression ratio tells you if daily moves are getting smaller (coiling)
- Gap stats tell you how often price jumps past your levels overnight
"""

import numpy as np
import pandas as pd


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range — measures how much a stock moves per day.

    True Range is the largest of:
    - Today's high minus today's low (intraday range)
    - Today's high minus yesterday's close (gap up then sell off)
    - Yesterday's close minus today's low (gap down then bounce)

    EXAMPLE: Stock closes at $100. Next day: high=$103, low=$98.
    TR = max(103-98, |103-100|, |98-100|) = max(5, 3, 2) = $5

    ATR smooths this over N days to get average daily movement.
    A stock with ATR=$2 and price=$100 has ATR% of 2%.
    """
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index — measures TREND STRENGTH (not direction).

    ADX doesn't tell you if price is going up or down.
    It tells you HOW STRONGLY it's trending in either direction.

    INTERPRETATION:
    - ADX < 20:  Weak trend / sideways → GOOD for range trading
    - ADX 20-25: Mild trend → acceptable
    - ADX 25-35: Strong trend → risky for range trading
    - ADX > 35:  Very strong trend → avoid range trading

    HOW IT WORKS:
    1. +DI measures upward movement strength
    2. -DI measures downward movement strength
    3. DX = difference between +DI and -DI (how one-sided the moves are)
    4. ADX = smoothed DX (stable trend strength reading)
    """
    plus_dm = high.diff()
    minus_dm = -low.diff()

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    atr = compute_atr(high, low, close, period)

    plus_di = 100 * (plus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr)

    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return adx


def compute_ema(series: pd.Series, period: int = 20) -> pd.Series:
    """Exponential Moving Average — a smoothed price line that reacts faster to recent prices.

    EXAMPLE: If price is $100, $102, $104, $103, $105...
    EMA(20) gives you a smooth line showing the "average direction"
    over the last 20 days, weighted toward recent prices.
    """
    return series.ewm(span=period, min_periods=period, adjust=False).mean()


def compute_ema_slope_pct(close: pd.Series, period: int = 20, slope_window: int = 20) -> float | None:
    """How much the EMA has moved over the last N days, as a percentage.

    EXAMPLE: EMA was $100 twenty days ago, now it's $103.
    Slope = (103 - 100) / 100 * 100 = 3%

    INTERPRETATION:
    - |slope| < 2%: Flat → good for range trading
    - |slope| 2-5%: Mild drift → acceptable
    - |slope| > 5%: Strong directional move → penalized
    """
    ema = compute_ema(close, period)
    if len(ema.dropna()) < slope_window:
        return None
    ema_recent = ema.iloc[-slope_window:]
    if ema_recent.iloc[0] == 0:
        return None
    return (ema_recent.iloc[-1] - ema_recent.iloc[0]) / ema_recent.iloc[0] * 100


def compute_atr_pct(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float | None:
    """ATR as a percentage of current price.

    EXAMPLE: Stock at $200 with ATR of $4 → ATR% = 2%
    This normalizes volatility so we can compare a $20 stock to a $500 stock.

    GOOD RANGE for range trading: 1-6% daily ATR.
    Too low (<1%): Dead stock, not worth trading
    Too high (>8%): Too chaotic, support/resistance unreliable
    """
    atr = compute_atr(high, low, close, period)
    latest_atr = atr.iloc[-1]
    latest_close = close.iloc[-1]
    if pd.isna(latest_atr) or latest_close <= 0:
        return None
    return latest_atr / latest_close * 100


def compute_compression_ratio(high: pd.Series, low: pd.Series, close: pd.Series) -> tuple[float, str]:
    """Detects whether volatility is coiling (compressing) or expanding.

    Compares short-term volatility (5 days) to longer-term (20 days).

    EXAMPLE: A stock normally moves $3/day (ATR20=$3).
    Last 5 days it only moved $1.5/day (ATR5=$1.5).
    Ratio = 1.5 / 3.0 = 0.5 → COMPRESSING

    WHY THIS MATTERS:
    - COMPRESSING near resistance: Price is coiling — breakout likely imminent
    - COMPRESSING near support: Breakdown coil — watch for downside
    - EXPANDING: Stock becoming more chaotic — range trading less reliable

    Returns (ratio, label).
    """
    atr_5 = compute_atr(high, low, close, period=5)
    atr_20 = compute_atr(high, low, close, period=20)
    latest_5 = atr_5.iloc[-1]
    latest_20 = atr_20.iloc[-1]

    if pd.isna(latest_5) or pd.isna(latest_20) or latest_20 <= 0:
        return 1.0, "NORMAL"

    ratio = latest_5 / latest_20

    if ratio < 0.7:
        label = "COMPRESSING"
    elif ratio > 1.3:
        label = "EXPANDING"
    else:
        label = "NORMAL"

    return round(ratio, 3), label


def compute_gap_stats(open_prices: pd.Series, close: pd.Series, threshold_pct: float = 2.0) -> tuple[float, float, float]:
    """Measures how often a stock "gaps" overnight.

    A gap = the stock opens significantly higher or lower than yesterday's close.
    This happens due to after-hours news, earnings, or market-wide moves.

    EXAMPLE: Stock closes at $100. Next day opens at $104.
    Gap = |104 - 100| / 100 = 4% → counts as a large gap.

    WHY THIS MATTERS FOR RANGE TRADING:
    If a stock gaps frequently, your support/resistance levels are less
    reliable because price can teleport past them overnight.

    EXAMPLE: You expect support at $98. But the stock gaps down to $94
    at the open — your stop-loss gets blown past before you can react.

    Returns (gap_frequency, avg_gap_pct, max_gap_pct).
    gap_frequency = fraction of days with gaps > threshold (e.g., 0.15 = 15% of days).
    """
    prev_close = close.shift(1)
    gap_pct = ((open_prices - prev_close) / prev_close * 100).abs()
    gap_pct = gap_pct.dropna()

    if len(gap_pct) == 0:
        return 0.0, 0.0, 0.0

    large_gaps = (gap_pct > threshold_pct).sum()
    frequency = large_gaps / len(gap_pct)
    avg = float(gap_pct.mean())
    max_gap = float(gap_pct.max())

    return frequency, avg, max_gap
