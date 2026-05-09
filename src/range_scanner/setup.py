"""Setup type classification: translates range state + context into actionable setup."""

from range_scanner.models import (
    BreakoutRisk, EdgePosition, SetupType, Verdict,
)
from range_scanner.context import MarketRegime, SectorRegime


def classify_setup(
    verdict: Verdict,
    edge_position: EdgePosition | None,
    breakout_risk: BreakoutRisk,
    market_regime: MarketRegime | None,
    sector_regime: SectorRegime | None,
    relative_strength_20d: float,
) -> SetupType:
    """Determine what kind of setup this is, given range state and context."""

    # Broken or non-range verdicts
    if verdict in (Verdict.BROKEN_UP, Verdict.BROKEN_DOWN, Verdict.TRENDING_NOT_RANGE,
                   Verdict.TOO_WIDE, Verdict.ILLIQUID, Verdict.INSUFFICIENT_DATA, Verdict.ERROR):
        return SetupType.NOT_RANGE_TRADE

    # No edge data = monitor only
    if edge_position is None:
        return SetupType.RANGE_MONITOR_ONLY

    # Broken positions
    if edge_position in (EdgePosition.BROKEN_UP, EdgePosition.BROKEN_DOWN):
        return SetupType.NOT_RANGE_TRADE

    # Mid-range = no edge, just monitor
    if edge_position in (EdgePosition.MID_RANGE, EdgePosition.UPPER_HALF, EdgePosition.LOWER_HALF):
        if edge_position == EdgePosition.UPPER_HALF and breakout_risk == BreakoutRisk.HIGH:
            return SetupType.BREAKOUT_WATCH_UPSIDE
        if edge_position == EdgePosition.LOWER_HALF and breakout_risk == BreakoutRisk.HIGH:
            return SetupType.BREAKDOWN_WATCH_DOWNSIDE
        return SetupType.RANGE_MONITOR_ONLY

    # Near support — potential long entry
    if edge_position == EdgePosition.NEAR_SUPPORT:
        return _classify_support_setup(
            market_regime, sector_regime, relative_strength_20d, breakout_risk
        )

    # Near resistance — potential short or breakout
    if edge_position == EdgePosition.NEAR_RESISTANCE:
        return _classify_resistance_setup(
            market_regime, sector_regime, relative_strength_20d, breakout_risk
        )

    return SetupType.RANGE_MONITOR_ONLY


def _classify_support_setup(
    market_regime: MarketRegime | None,
    sector_regime: SectorRegime | None,
    rs_20d: float,
    breakout_risk: BreakoutRisk,
) -> SetupType:
    """Near support: is this a bounce candidate or avoid?"""

    # Very weak RS in a strong market = support may fail
    if rs_20d < -10 and market_regime == MarketRegime.RISK_ON_TRENDING:
        return SetupType.AVOID_CONTEXT_CONFLICT

    # Sector breaking down = support fragile
    if sector_regime == SectorRegime.TRENDING_DOWN and rs_20d < -5:
        return SetupType.AVOID_CONTEXT_CONFLICT

    # High breakdown risk with volume
    if breakout_risk == BreakoutRisk.HIGH:
        return SetupType.BREAKDOWN_WATCH_DOWNSIDE

    # Good context: calm market or RS is positive
    if market_regime in (MarketRegime.CALM_RANGE_FRIENDLY, MarketRegime.MIXED):
        return SetupType.MEAN_REVERSION_LONG

    # Risk-on market, RS is acceptable
    if market_regime == MarketRegime.RISK_ON_TRENDING and rs_20d > -5:
        return SetupType.MEAN_REVERSION_LONG

    # Risk-off volatile — support bounces can work if RS is ok
    if market_regime == MarketRegime.RISK_OFF_VOLATILE and rs_20d > 0:
        return SetupType.MEAN_REVERSION_LONG

    return SetupType.RANGE_MONITOR_ONLY


def _classify_resistance_setup(
    market_regime: MarketRegime | None,
    sector_regime: SectorRegime | None,
    rs_20d: float,
    breakout_risk: BreakoutRisk,
) -> SetupType:
    """Near resistance: is this a short candidate, breakout watch, or avoid?"""

    # Risk-on + sector trending up = breakout more likely
    if market_regime == MarketRegime.RISK_ON_TRENDING and sector_regime in (
        SectorRegime.TRENDING_UP, SectorRegime.STABLE
    ):
        return SetupType.BREAKOUT_WATCH_UPSIDE

    # Strong RS + high breakout risk = breakout watch
    if rs_20d > 5 and breakout_risk in (BreakoutRisk.HIGH, BreakoutRisk.MODERATE):
        return SetupType.BREAKOUT_WATCH_UPSIDE

    # Calm market + weak breakout risk = mean reversion short
    if market_regime == MarketRegime.CALM_RANGE_FRIENDLY and breakout_risk == BreakoutRisk.LOW:
        return SetupType.MEAN_REVERSION_SHORT

    # Risk-off + near resistance = possible short
    if market_regime == MarketRegime.RISK_OFF_VOLATILE:
        return SetupType.MEAN_REVERSION_SHORT

    # Mixed / sector stable / low risk
    if sector_regime == SectorRegime.TRENDING_DOWN:
        return SetupType.MEAN_REVERSION_SHORT

    return SetupType.RANGE_MONITOR_ONLY


def compute_context_score(
    market_regime: MarketRegime | None,
    sector_regime: SectorRegime | None,
    relative_strength_20d: float,
    setup_type: SetupType,
) -> float:
    """0-100 context score: how favorable is the environment for this setup?"""
    if setup_type == SetupType.NOT_RANGE_TRADE:
        return 0.0

    score = 50.0  # baseline

    # Market regime contribution
    if market_regime == MarketRegime.CALM_RANGE_FRIENDLY:
        score += 20
    elif market_regime == MarketRegime.MIXED:
        score += 5
    elif market_regime == MarketRegime.RISK_ON_TRENDING:
        if setup_type in (SetupType.BREAKOUT_WATCH_UPSIDE, SetupType.MEAN_REVERSION_LONG):
            score += 10
        else:
            score -= 10
    elif market_regime == MarketRegime.RISK_OFF_VOLATILE:
        if setup_type == SetupType.MEAN_REVERSION_SHORT:
            score += 10
        else:
            score -= 15

    # Sector alignment
    if sector_regime == SectorRegime.STABLE:
        score += 15
    elif sector_regime == SectorRegime.TRENDING_UP:
        if setup_type in (SetupType.BREAKOUT_WATCH_UPSIDE, SetupType.MEAN_REVERSION_LONG):
            score += 15
        else:
            score -= 10
    elif sector_regime == SectorRegime.TRENDING_DOWN:
        if setup_type in (SetupType.MEAN_REVERSION_SHORT, SetupType.BREAKDOWN_WATCH_DOWNSIDE):
            score += 10
        else:
            score -= 15
    elif sector_regime == SectorRegime.VOLATILE:
        score -= 10

    # RS alignment
    if setup_type in (SetupType.MEAN_REVERSION_LONG, SetupType.BREAKOUT_WATCH_UPSIDE):
        if relative_strength_20d > 3:
            score += 10
        elif relative_strength_20d < -5:
            score -= 15
    elif setup_type in (SetupType.MEAN_REVERSION_SHORT, SetupType.BREAKDOWN_WATCH_DOWNSIDE):
        if relative_strength_20d < -3:
            score += 10
        elif relative_strength_20d > 5:
            score -= 15

    # Avoid conflicts get penalized
    if setup_type == SetupType.AVOID_CONTEXT_CONFLICT:
        score = min(score, 25.0)

    return round(max(0.0, min(100.0, score)), 1)
