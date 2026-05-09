import numpy as np
import pandas as pd


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
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
    return series.ewm(span=period, min_periods=period, adjust=False).mean()


def compute_ema_slope_pct(close: pd.Series, period: int = 20, slope_window: int = 20) -> float | None:
    ema = compute_ema(close, period)
    if len(ema.dropna()) < slope_window:
        return None
    ema_recent = ema.iloc[-slope_window:]
    if ema_recent.iloc[0] == 0:
        return None
    return (ema_recent.iloc[-1] - ema_recent.iloc[0]) / ema_recent.iloc[0] * 100


def compute_atr_pct(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float | None:
    atr = compute_atr(high, low, close, period)
    latest_atr = atr.iloc[-1]
    latest_close = close.iloc[-1]
    if pd.isna(latest_atr) or latest_close <= 0:
        return None
    return latest_atr / latest_close * 100


def compute_compression_ratio(high: pd.Series, low: pd.Series, close: pd.Series) -> tuple[float, str]:
    """Compute ATR(5) / ATR(20) to detect volatility compression/expansion.
    Returns (ratio, label). Ratio < 0.7 = compressing, > 1.3 = expanding."""
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
    """Compute gap statistics from open vs prior close.
    Returns (gap_frequency, avg_gap_pct, max_gap_pct).
    gap_frequency = fraction of days with gaps > threshold."""
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
