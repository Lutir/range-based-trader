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


def cluster_prices_weighted(
    pivots: list[tuple[int, float]], tolerance_pct: float, total_bars: int
) -> list[list[tuple[int, float]]]:
    """Cluster pivot prices, preserving index for recency weighting."""
    if not pivots:
        return []
    sorted_pivots = sorted(pivots, key=lambda x: x[1])
    clusters: list[list[tuple[int, float]]] = [[sorted_pivots[0]]]
    for pivot in sorted_pivots[1:]:
        cluster_prices = [p[1] for p in clusters[-1]]
        cluster_mid = np.mean(cluster_prices)
        if abs(pivot[1] - cluster_mid) / cluster_mid * 100 <= tolerance_pct:
            clusters[-1].append(pivot)
        else:
            clusters.append([pivot])
    return clusters


def select_zone_weighted(
    clusters: list[list[tuple[int, float]]], total_bars: int
) -> tuple[float, float] | None:
    """Select best zone using recency-weighted scoring. Returns (zone_price, zone_score)."""
    if not clusters:
        return None
    best_score = -1.0
    best_price = 0.0
    for cluster in clusters:
        recency_weights = [0.5 + 0.5 * (idx / total_bars) for idx, _ in cluster]
        score = sum(recency_weights)
        if score > best_score:
            best_score = score
            prices = [p for _, p in cluster]
            best_price = float(np.mean(prices))
    return best_price, best_score


def count_touches_with_strength(
    df: pd.DataFrame, zone: float, tolerance_pct: float, side: str
) -> tuple[int, float]:
    """Count touches and measure average reaction strength (% move away from zone)."""
    zone_low = zone * (1 - tolerance_pct / 100)
    zone_high = zone * (1 + tolerance_pct / 100)
    touches = 0
    reaction_magnitudes: list[float] = []

    for i in range(len(df)):
        row = df.iloc[i]
        is_touch = False

        if side == "support":
            if zone_low <= row["low"] <= zone_high and row["close"] > zone:
                is_touch = True
        else:
            if zone_low <= row["high"] <= zone_high and row["close"] < zone:
                is_touch = True

        if is_touch:
            touches += 1
            # Measure reaction: how far did close move from zone?
            if side == "support":
                reaction = (row["close"] - zone) / zone * 100
            else:
                reaction = (zone - row["close"]) / zone * 100
            reaction_magnitudes.append(reaction)

    avg_reaction = float(np.mean(reaction_magnitudes)) if reaction_magnitudes else 0.0
    return touches, avg_reaction


def compute_containment_ratio(close: pd.Series, support: float, resistance: float) -> float:
    inside = ((close >= support) & (close <= resistance)).sum()
    return inside / len(close)


def compute_rotation_count(close: pd.Series, support: float, resistance: float) -> int:
    """Count full rotations: price crossing from one zone toward the other.
    A rotation = close moves from lower third to upper third or vice versa."""
    range_size = resistance - support
    lower_third = support + range_size * 0.33
    upper_third = resistance - range_size * 0.33

    rotations = 0
    last_zone = None

    for c in close:
        if c <= lower_third:
            current_zone = "low"
        elif c >= upper_third:
            current_zone = "high"
        else:
            continue

        if last_zone is not None and current_zone != last_zone:
            rotations += 1
        last_zone = current_zone

    return rotations


def compute_range_tightness(close: pd.Series, support: float, resistance: float) -> float:
    """Measure how tightly closes cluster around midpoint relative to range width.
    Returns 0-1 where 1 = very tight oscillation, 0 = spread across full range."""
    midpoint = (support + resistance) / 2
    range_width = resistance - support
    if range_width <= 0:
        return 0.0
    inside_closes = close[(close >= support) & (close <= resistance)]
    if len(inside_closes) < 5:
        return 0.0
    stddev = inside_closes.std()
    # Normalize: stddev relative to half the range width
    # Perfect oscillation edge-to-edge has stddev ~ 0.29 * range (uniform)
    # Tight clustering around midpoint has low stddev
    # We want high stddev (using full range) = good rotational behavior
    normalized = stddev / (range_width * 0.5)
    return min(normalized, 1.0)


def detect_higher_highs_lows(pivot_highs: list[tuple[int, float]], pivot_lows: list[tuple[int, float]]) -> float:
    """Detect trending structure via consecutive higher-highs/higher-lows or lower pattern.
    Returns a leakage score 0-1 where 1 = strong sequential trend."""
    hh_count = 0
    hl_count = 0
    lh_count = 0
    ll_count = 0

    highs = [p for _, p in pivot_highs]
    lows = [p for _, p in pivot_lows]

    for i in range(1, len(highs)):
        if highs[i] > highs[i - 1]:
            hh_count += 1
        elif highs[i] < highs[i - 1]:
            lh_count += 1

    for i in range(1, len(lows)):
        if lows[i] > lows[i - 1]:
            hl_count += 1
        elif lows[i] < lows[i - 1]:
            ll_count += 1

    total_h = max(len(highs) - 1, 1)
    total_l = max(len(lows) - 1, 1)

    # Uptrend: higher-highs AND higher-lows
    up_leakage = (hh_count / total_h) * (hl_count / total_l)
    # Downtrend: lower-highs AND lower-lows
    down_leakage = (lh_count / total_h) * (ll_count / total_l)

    return max(up_leakage, down_leakage)


def detect_false_breaks(df: pd.DataFrame, support: float, resistance: float, tolerance_pct: float) -> tuple[int, int]:
    """Count false breakouts — price breaks a level then closes back inside.

    A FALSE BREAK (also called a "fakeout" or "trap") happens when:
    - Price pokes ABOVE resistance (wick goes higher) but CLOSES back below it
    - Price pokes BELOW support (wick goes lower) but CLOSES back above it

    WHY THIS MATTERS:
    False breaks actually VALIDATE the range. If price tried to break out
    and failed, it means there's real selling at resistance or buying at support.

    EXAMPLE (bull trap at resistance):
      Resistance = $110. One day the high reaches $112 (broke above!)
      But by the close, price settles at $109 (closed back inside).
      This is a "bull trap" — longs who bought the breakout got trapped.
      It confirms $110 resistance is strong.

    EXAMPLE (bear trap at support):
      Support = $100. One day the low drops to $98 (broke below!)
      But by the close, price recovers to $101 (closed back inside).
      This is a "bear trap" — shorts got trapped.
      It confirms $100 support is strong.

    Returns (resistance_false_breaks, support_false_breaks).
    Higher counts = stronger zone validation.
    """
    res_tolerance = resistance * (1 + tolerance_pct / 100)
    sup_tolerance = support * (1 - tolerance_pct / 100)

    resistance_traps = 0
    support_traps = 0

    for i in range(1, len(df)):
        row = df.iloc[i]
        # Bull trap: high broke above resistance but close came back inside
        if row["high"] > resistance and row["close"] <= resistance:
            resistance_traps += 1
        # Bear trap: low broke below support but close came back inside
        if row["low"] < support and row["close"] >= support:
            support_traps += 1

    return resistance_traps, support_traps


def detect_range_structure(df: pd.DataFrame, config: ScannerConfig) -> RangeStructure | None:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    total_bars = len(df)

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

    high_clusters = cluster_prices_weighted(pivot_highs, tolerance_pct, total_bars)
    low_clusters = cluster_prices_weighted(pivot_lows, tolerance_pct, total_bars)

    resistance_result = select_zone_weighted(high_clusters, total_bars)
    support_result = select_zone_weighted(low_clusters, total_bars)

    if resistance_result is None or support_result is None:
        return None

    resistance = resistance_result[0]
    support = support_result[0]

    if resistance <= support:
        return None

    range_width_pct = (resistance - support) / support * 100

    support_touches, support_reaction = count_touches_with_strength(df, support, tolerance_pct, "support")
    resistance_touches, resistance_reaction = count_touches_with_strength(df, resistance, tolerance_pct, "resistance")
    containment_ratio = compute_containment_ratio(close, support, resistance)
    rotation_count = compute_rotation_count(close, support, resistance)
    tightness = compute_range_tightness(close, support, resistance)
    trend_leakage = detect_higher_highs_lows(pivot_highs, pivot_lows)
    res_false_breaks, sup_false_breaks = detect_false_breaks(df, support, resistance, tolerance_pct)

    return RangeStructure(
        support=round(support, 2),
        resistance=round(resistance, 2),
        range_width_pct=round(range_width_pct, 2),
        support_touches=support_touches,
        resistance_touches=resistance_touches,
        containment_ratio=round(containment_ratio, 4),
        rotation_count=rotation_count,
        support_reaction_strength=round(support_reaction, 4),
        resistance_reaction_strength=round(resistance_reaction, 4),
        tightness=round(tightness, 4),
        trend_leakage=round(trend_leakage, 4),
        resistance_false_breaks=res_false_breaks,
        support_false_breaks=sup_false_breaks,
    )
