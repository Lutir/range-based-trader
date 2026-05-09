import pandas as pd

from range_scanner.models import BreakoutRisk, EdgePosition


def compute_position_in_range(latest_close: float, support: float, resistance: float) -> float:
    if resistance == support:
        return 0.5
    return (latest_close - support) / (resistance - support)


def classify_edge_position(position: float) -> EdgePosition:
    if position > 1.0:
        return EdgePosition.BROKEN_UP
    if position < 0.0:
        return EdgePosition.BROKEN_DOWN
    if position >= 0.80:
        return EdgePosition.NEAR_RESISTANCE
    if position >= 0.60:
        return EdgePosition.UPPER_HALF
    if position >= 0.40:
        return EdgePosition.MID_RANGE
    if position >= 0.20:
        return EdgePosition.LOWER_HALF
    return EdgePosition.NEAR_SUPPORT


def assess_breakout_risk(
    df: pd.DataFrame, position: float, support: float, resistance: float
) -> BreakoutRisk:
    """Assess breakout/breakdown risk based on position, volume, and recent direction."""
    if 0.20 <= position <= 0.80:
        return BreakoutRisk.LOW

    close = df["close"]
    volume = df["volume"]

    vol_5d = volume.iloc[-5:].mean()
    vol_20d = volume.iloc[-20:].mean()
    volume_elevated = vol_5d > vol_20d * 1.25

    recent_5 = close.iloc[-5:]
    direction_up = recent_5.iloc[-1] > recent_5.iloc[0]
    direction_down = recent_5.iloc[-1] < recent_5.iloc[0]

    # Near resistance — upside breakout risk
    if position >= 0.80:
        if volume_elevated and direction_up:
            return BreakoutRisk.HIGH
        if volume_elevated or direction_up:
            return BreakoutRisk.MODERATE
        return BreakoutRisk.LOW

    # Near support — downside breakdown risk
    if position <= 0.20:
        if volume_elevated and direction_down:
            return BreakoutRisk.HIGH
        if volume_elevated or direction_down:
            return BreakoutRisk.MODERATE
        return BreakoutRisk.LOW

    return BreakoutRisk.LOW


def compute_entry_quality(position: float, edge_position: EdgePosition, breakout_risk: BreakoutRisk) -> float:
    """Score 0-100: how actionable is this as a range entry right now?
    Best entries are near edges with low breakout risk."""
    if edge_position in (EdgePosition.BROKEN_UP, EdgePosition.BROKEN_DOWN):
        return 0.0

    # Distance from nearest edge (0 = at edge, 0.5 = mid-range)
    distance_from_edge = min(position, 1.0 - position)
    # Closer to edge = better entry
    edge_score = max(0, (0.5 - distance_from_edge) / 0.5) * 100

    # Penalize high breakout risk
    if breakout_risk == BreakoutRisk.HIGH:
        edge_score *= 0.4
    elif breakout_risk == BreakoutRisk.MODERATE:
        edge_score *= 0.7

    return round(min(edge_score, 100.0), 1)
