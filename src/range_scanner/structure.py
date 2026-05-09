import numpy as np
import pandas as pd

from range_scanner.config import ScannerConfig
from range_scanner.indicators import compute_atr
from range_scanner.models import RangeStructure


def find_pivot_highs(high: pd.Series, window: int = 3) -> list[tuple[int, float]]:
    pivots = []
    for i in range(window, len(high) - window):
        if high.iloc[i] == high.iloc[i - window:i + window + 1].max():
            pivots.append((i, high.iloc[i]))
    return pivots


def find_pivot_lows(low: pd.Series, window: int = 3) -> list[tuple[int, float]]:
    pivots = []
    for i in range(window, len(low) - window):
        if low.iloc[i] == low.iloc[i - window:i + window + 1].min():
            pivots.append((i, low.iloc[i]))
    return pivots


def cluster_prices(prices: list[float], tolerance_pct: float) -> list[list[float]]:
    if not prices:
        return []
    sorted_prices = sorted(prices)
    clusters: list[list[float]] = [[sorted_prices[0]]]
    for price in sorted_prices[1:]:
        cluster_mid = np.mean(clusters[-1])
        if abs(price - cluster_mid) / cluster_mid * 100 <= tolerance_pct:
            clusters[-1].append(price)
        else:
            clusters.append([price])
    return clusters


def select_zone(clusters: list[list[float]], mode: str) -> float | None:
    if not clusters:
        return None
    best = max(clusters, key=len)
    return float(np.mean(best))


def count_touches(
    df: pd.DataFrame, zone: float, tolerance_pct: float, side: str
) -> int:
    zone_low = zone * (1 - tolerance_pct / 100)
    zone_high = zone * (1 + tolerance_pct / 100)
    touches = 0

    if side == "support":
        for _, row in df.iterrows():
            if zone_low <= row["low"] <= zone_high and row["close"] > zone:
                touches += 1
    else:
        for _, row in df.iterrows():
            if zone_low <= row["high"] <= zone_high and row["close"] < zone:
                touches += 1
    return touches


def compute_containment_ratio(close: pd.Series, support: float, resistance: float) -> float:
    inside = ((close >= support) & (close <= resistance)).sum()
    return inside / len(close)


def detect_range_structure(df: pd.DataFrame, config: ScannerConfig) -> RangeStructure | None:
    high = df["high"]
    low = df["low"]
    close = df["close"]

    atr = compute_atr(high, low, close, config.atr_period)
    latest_atr = atr.iloc[-1]
    latest_close = close.iloc[-1]
    if pd.isna(latest_atr) or latest_close <= 0:
        return None

    atr_pct = latest_atr / latest_close * 100
    tolerance_pct = max(config.zone_tolerance_atr_mult * atr_pct, config.zone_tolerance_min_pct)

    pivot_highs = find_pivot_highs(high, config.pivot_window)
    pivot_lows = find_pivot_lows(low, config.pivot_window)

    if len(pivot_highs) < 2 or len(pivot_lows) < 2:
        return None

    high_prices = [p for _, p in pivot_highs]
    low_prices = [p for _, p in pivot_lows]

    high_clusters = cluster_prices(high_prices, tolerance_pct)
    low_clusters = cluster_prices(low_prices, tolerance_pct)

    resistance = select_zone(high_clusters, "resistance")
    support = select_zone(low_clusters, "support")

    if support is None or resistance is None or resistance <= support:
        return None

    range_width_pct = (resistance - support) / support * 100

    support_touches = count_touches(df, support, tolerance_pct, "support")
    resistance_touches = count_touches(df, resistance, tolerance_pct, "resistance")
    containment_ratio = compute_containment_ratio(close, support, resistance)

    return RangeStructure(
        support=round(support, 2),
        resistance=round(resistance, 2),
        range_width_pct=round(range_width_pct, 2),
        support_touches=support_touches,
        resistance_touches=resistance_touches,
        containment_ratio=round(containment_ratio, 4),
    )
