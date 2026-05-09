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
