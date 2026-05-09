"""
Range state classification: WHERE is price right now within the range?

This module answers: "Even if the range is good, is NOW a good time?"

ANALOGY: Think of a range like a tennis court.
- Support = baseline on one side
- Resistance = baseline on the other side
- Mid-range = the net area

The best "entries" happen near the baselines (edges), not at the net.
If you're at the net (mid-range), you just wait and watch.

EXAMPLE:
  Stock: ADSK
  Support: $229, Resistance: $247
  Current price: $245 (position = 0.89 → NEAR_RESISTANCE)

  The scanner says: "Good range, but price is near the ceiling.
  Don't buy here expecting a bounce — you'd be buying near resistance."

POSITION VALUES:
  0.00 = exactly at support
  0.50 = dead center (mid-range)
  1.00 = exactly at resistance
  >1.0 = broken above resistance
  <0.0 = broken below support
"""

import pandas as pd

from range_scanner.models import BreakoutRisk, EdgePosition


def compute_position_in_range(latest_close: float, support: float, resistance: float) -> float:
    """Where is the current price between support (0.0) and resistance (1.0)?

    EXAMPLE: Support=$100, Resistance=$110, Price=$107
    Position = (107-100) / (110-100) = 0.70 → in the upper half
    """
    if resistance == support:
        return 0.5
    return (latest_close - support) / (resistance - support)


def classify_edge_position(position: float) -> EdgePosition:
    """Convert numeric position into a human-readable zone label.

    Think of the range divided into 5 zones:

    |  NEAR_SUPPORT  |  LOWER_HALF  |  MID_RANGE  |  UPPER_HALF  |  NEAR_RESISTANCE  |
    0.0            0.20           0.40          0.60           0.80              1.00
    """
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
    """Is price about to break out of the range?

    Checks two signals:
    1. VOLUME: Are recent 5 days trading 25%+ more than the 20-day average?
       (Big volume near edges often precedes breakouts)
    2. DIRECTION: Is price moving TOWARD the nearby edge?
       (Momentum pushing against the boundary)

    EXAMPLE: Stock near resistance ($110), last 5 days volume is 40% above average,
    and price has been rising → HIGH breakout risk (likely to push through $110)

    If price is mid-range (between 0.20 and 0.80), breakout risk is always LOW
    because it's not close enough to either edge to matter.
    """
    if 0.20 <= position <= 0.80:
        return BreakoutRisk.LOW

    close = df["close"]
    volume = df["volume"]

    # Is recent volume elevated? (buying/selling pressure building)
    vol_5d = volume.iloc[-5:].mean()
    vol_20d = volume.iloc[-20:].mean()
    volume_elevated = vol_5d > vol_20d * 1.25

    # Is price moving toward the edge?
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
    """How good is this moment for a range trade entry? (0-100)

    BEST ENTRIES: Near an edge (support or resistance) with low breakout risk.
    WORST ENTRIES: Mid-range (nowhere to go), or near edge with HIGH breakout risk.

    EXAMPLE:
    - Price at support, breakout risk LOW → Entry quality 100 (buy the bounce!)
    - Price at resistance, breakout risk HIGH → Entry quality 40 (might break out)
    - Price mid-range → Entry quality ~0 (nothing to do, just watch)

    The math:
    - Closer to an edge = higher score (max at 0.0 or 1.0)
    - Mid-range (0.5) = zero score
    - High breakout risk multiplies by 0.4 (heavy penalty)
    - Moderate breakout risk multiplies by 0.7
    """
    if edge_position in (EdgePosition.BROKEN_UP, EdgePosition.BROKEN_DOWN):
        return 0.0

    # How far from the nearest edge? (0 = at edge, 0.5 = dead center)
    distance_from_edge = min(position, 1.0 - position)
    # Convert: at edge (0) → score 100, at center (0.5) → score 0
    edge_score = max(0, (0.5 - distance_from_edge) / 0.5) * 100

    # Penalize if the edge might break
    if breakout_risk == BreakoutRisk.HIGH:
        edge_score *= 0.4
    elif breakout_risk == BreakoutRisk.MODERATE:
        edge_score *= 0.7

    return round(min(edge_score, 100.0), 1)
