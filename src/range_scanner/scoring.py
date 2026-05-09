from range_scanner.config import ScannerConfig
from range_scanner.models import RangeStructure, ScoreBreakdown, Verdict


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def score_liquidity(avg_dollar_volume: float, config: ScannerConfig) -> float:
    if avg_dollar_volume < config.min_dollar_volume:
        return 0.0
    ratio = avg_dollar_volume / config.min_dollar_volume
    if ratio >= 10:
        return 100.0
    return _clamp((ratio - 1) / 9 * 100)


def score_range_width(range_width_pct: float) -> float:
    """Tight sweet spot: 3-8% ideal. Hard penalty >12%, reject >25%."""
    if range_width_pct < 2:
        return _clamp(range_width_pct / 2 * 30)
    if range_width_pct <= 3:
        return _clamp(30 + (range_width_pct - 2) * 40)
    if range_width_pct <= 8:
        return 100.0
    if range_width_pct <= 12:
        return _clamp(100 - (range_width_pct - 8) / 4 * 70)
    if range_width_pct <= 15:
        return _clamp(30 - (range_width_pct - 12) / 3 * 20)
    if range_width_pct <= 25:
        return _clamp(10 - (range_width_pct - 15) / 10 * 10)
    return 0.0


def score_touches(touches: int, max_benefit: int = 4) -> float:
    if touches < 2:
        return _clamp(touches * 20)
    effective = min(touches, max_benefit)
    return _clamp(20 + (effective - 1) / (max_benefit - 1) * 80)


def score_reaction_strength(avg_reaction_pct: float) -> float:
    if avg_reaction_pct >= 2.0:
        return 100.0
    if avg_reaction_pct >= 1.0:
        return _clamp(50 + (avg_reaction_pct - 1.0) * 50)
    if avg_reaction_pct >= 0.5:
        return _clamp(20 + (avg_reaction_pct - 0.5) / 0.5 * 30)
    return _clamp(avg_reaction_pct / 0.5 * 20)


def score_containment(containment_ratio: float) -> float:
    if containment_ratio >= 0.85:
        return 100.0
    if containment_ratio >= 0.70:
        return _clamp(50 + (containment_ratio - 0.70) / 0.15 * 50)
    return _clamp(containment_ratio / 0.70 * 50)


def score_rotation(rotation_count: int) -> float:
    if rotation_count >= 8:
        return 100.0
    if rotation_count >= 5:
        return _clamp(70 + (rotation_count - 5) / 3 * 30)
    if rotation_count >= 3:
        return _clamp(40 + (rotation_count - 3) / 2 * 30)
    if rotation_count >= 1:
        return _clamp(rotation_count * 20)
    return 0.0


def score_tightness(tightness: float) -> float:
    if tightness >= 0.5:
        return 100.0
    if tightness >= 0.3:
        return _clamp(50 + (tightness - 0.3) / 0.2 * 50)
    return _clamp(tightness / 0.3 * 50)


def score_adx(adx: float) -> float:
    if adx < 20:
        return 100.0
    if adx <= 25:
        return _clamp(100 - (adx - 20) / 5 * 40)
    if adx <= 35:
        return _clamp(60 - (adx - 25) / 10 * 50)
    return _clamp(10 - (adx - 35) / 10 * 10)


def score_ema_slope(abs_slope_pct: float) -> float:
    if abs_slope_pct < 2:
        return 100.0
    if abs_slope_pct <= 5:
        return _clamp(100 - (abs_slope_pct - 2) / 3 * 70)
    return _clamp(30 - (abs_slope_pct - 5) / 5 * 30)


def score_trend_leakage(leakage: float) -> float:
    if leakage <= 0.15:
        return 100.0
    if leakage <= 0.35:
        return _clamp(100 - (leakage - 0.15) / 0.20 * 50)
    if leakage <= 0.60:
        return _clamp(50 - (leakage - 0.35) / 0.25 * 40)
    return _clamp(10 - (leakage - 0.60) / 0.40 * 10)


def score_atr_stability(atr_pct: float) -> float:
    if 1 <= atr_pct <= 6:
        return 100.0
    if atr_pct < 1:
        return _clamp(atr_pct / 1 * 60)
    if atr_pct <= 8:
        return _clamp(100 - (atr_pct - 6) / 2 * 50)
    return _clamp(50 - (atr_pct - 8) / 4 * 40)


def compute_score(
    structure: RangeStructure,
    adx: float,
    atr_pct: float,
    ema_slope_pct: float,
    avg_dollar_volume: float,
    config: ScannerConfig,
) -> ScoreBreakdown:
    liq = score_liquidity(avg_dollar_volume, config)
    rw = score_range_width(structure.range_width_pct)
    st = score_touches(structure.support_touches, config.touch_max_benefit)
    rt = score_touches(structure.resistance_touches, config.touch_max_benefit)
    sr = score_reaction_strength(structure.support_reaction_strength)
    rr = score_reaction_strength(structure.resistance_reaction_strength)
    cont = score_containment(structure.containment_ratio)
    rot = score_rotation(structure.rotation_count)
    tight = score_tightness(structure.tightness)
    adx_s = score_adx(adx)
    ema_s = score_ema_slope(abs(ema_slope_pct))
    trend_s = score_trend_leakage(structure.trend_leakage)
    atr_s = score_atr_stability(atr_pct)

    # Weight distribution:
    # Rotation + reaction = 30% (core "is this a real range?" signal)
    # Structure quality = 25% (containment + tightness + range width)
    # Anti-trend = 20% (ADX + EMA slope + trend leakage)
    # Touches = 10%
    # Liquidity + ATR = 10% (filter, not differentiator)
    # Minimum rotation gate = 5% bonus/penalty
    total = (
        rot * 20 / 100
        + ((sr + rr) / 2) * 10 / 100
        + cont * 10 / 100
        + tight * 8 / 100
        + rw * 7 / 100
        + st * 5 / 100
        + rt * 5 / 100
        + adx_s * 10 / 100
        + ema_s * 5 / 100
        + trend_s * 10 / 100
        + liq * 5 / 100
        + atr_s * 5 / 100
    )

    # Hard width cap: wide ranges cannot score as excellent regardless of other metrics
    if structure.range_width_pct > 25:
        total = min(total, 30.0)
    elif structure.range_width_pct > 15:
        total = min(total, 50.0)
    elif structure.range_width_pct > 12:
        total = min(total, 65.0)

    # Minimum rotation requirement: no rotations = hard cap
    if structure.rotation_count < 2:
        total = min(total, 55.0)

    total = _clamp(total)

    return ScoreBreakdown(
        liquidity_score=round(liq, 2),
        range_width_score=round(rw, 2),
        support_touch_score=round(st, 2),
        resistance_touch_score=round(rt, 2),
        containment_score=round(cont, 2),
        rotation_score=round(rot, 2),
        reaction_score=round((sr + rr) / 2, 2),
        tightness_score=round(tight, 2),
        adx_score=round(adx_s, 2),
        ema_slope_score=round(ema_s, 2),
        trend_leakage_score=round(trend_s, 2),
        atr_stability_score=round(atr_s, 2),
        total=round(total, 2),
    )


def compute_sub_scores(breakdown: ScoreBreakdown) -> tuple[float, float, float]:
    """Compute explainable sub-scores: (structure, regime, liquidity)."""
    structure = (
        breakdown.rotation_score * 0.30
        + breakdown.reaction_score * 0.20
        + breakdown.containment_score * 0.20
        + breakdown.tightness_score * 0.15
        + breakdown.range_width_score * 0.15
    )
    regime = (
        breakdown.adx_score * 0.40
        + breakdown.ema_slope_score * 0.25
        + breakdown.trend_leakage_score * 0.35
    )
    liquidity = (
        breakdown.liquidity_score * 0.60
        + breakdown.atr_stability_score * 0.40
    )
    return round(structure, 1), round(regime, 1), round(liquidity, 1)


def classify_verdict(
    score: float, adx: float, ema_slope_pct: float,
    trend_leakage: float, range_width_pct: float, rotation_count: int,
    edge_position: "EdgePosition | None" = None,
    breakout_risk: "BreakoutRisk | None" = None,
) -> Verdict:
    from range_scanner.models import BreakoutRisk, EdgePosition

    # Hard gates first — broken ranges
    if edge_position == EdgePosition.BROKEN_UP:
        return Verdict.BROKEN_UP
    if edge_position == EdgePosition.BROKEN_DOWN:
        return Verdict.BROKEN_DOWN

    # Trend gates
    if adx > 30 or abs(ema_slope_pct) > 6 or trend_leakage > 0.5:
        return Verdict.TRENDING_NOT_RANGE
    if range_width_pct > 25:
        return Verdict.TOO_WIDE
    if range_width_pct > 15:
        return Verdict.WIDE_RANGE

    # Score-based classification with edge awareness
    is_good_range = score >= 55 and rotation_count >= 3

    if is_good_range and edge_position == EdgePosition.NEAR_RESISTANCE:
        return Verdict.RANGE_PRESSING_RESISTANCE
    if is_good_range and edge_position == EdgePosition.NEAR_SUPPORT:
        return Verdict.RANGE_PRESSING_SUPPORT

    if score >= 75 and adx < 25 and rotation_count >= 3:
        return Verdict.EXCELLENT_RANGE
    if score >= 55:
        return Verdict.WATCHLIST
    if score >= 35:
        return Verdict.MESSY_RANGE
    return Verdict.MESSY_RANGE


def generate_reason(
    structure: RangeStructure, adx: float, ema_slope_pct: float, verdict: Verdict,
    edge_position: "EdgePosition | None" = None, entry_quality: float | None = None,
    breakout_risk: "BreakoutRisk | None" = None,
) -> str:
    """Generate human-readable explanation for the verdict."""
    from range_scanner.models import BreakoutRisk, EdgePosition

    parts: list[str] = []

    if structure.rotation_count >= 5:
        parts.append(f"{structure.rotation_count} rotations (strong)")
    elif structure.rotation_count >= 3:
        parts.append(f"{structure.rotation_count} rotations (adequate)")
    else:
        parts.append(f"Only {structure.rotation_count} rotations (weak)")

    if structure.range_width_pct > 15:
        parts.append(f"width {structure.range_width_pct:.1f}% (too wide)")
    elif structure.range_width_pct > 10:
        parts.append(f"width {structure.range_width_pct:.1f}% (wide)")
    elif structure.range_width_pct >= 3:
        parts.append(f"width {structure.range_width_pct:.1f}% (good)")
    else:
        parts.append(f"width {structure.range_width_pct:.1f}% (tight)")

    if verdict == Verdict.TRENDING_NOT_RANGE:
        if adx > 30:
            parts.append(f"ADX {adx:.0f} (trending)")
        if abs(ema_slope_pct) > 6:
            parts.append(f"EMA slope {ema_slope_pct:.1f}% (directional)")
        if structure.trend_leakage > 0.5:
            parts.append(f"trend leakage {structure.trend_leakage:.0%}")

    avg_reaction = (structure.support_reaction_strength + structure.resistance_reaction_strength) / 2
    if avg_reaction >= 1.5:
        parts.append("strong reactions")
    elif avg_reaction < 0.5:
        parts.append("weak reactions")

    # False-break validation
    total_traps = structure.resistance_false_breaks + structure.support_false_breaks
    if total_traps >= 3:
        parts.append(f"{total_traps} false breaks (zones validated)")
    elif total_traps >= 1:
        parts.append(f"{total_traps} false break(s)")

    # Edge position context
    if edge_position == EdgePosition.BROKEN_UP:
        parts.append("BROKEN above resistance")
    elif edge_position == EdgePosition.BROKEN_DOWN:
        parts.append("BROKEN below support")
    elif edge_position == EdgePosition.NEAR_RESISTANCE:
        parts.append("price near resistance")
    elif edge_position == EdgePosition.NEAR_SUPPORT:
        parts.append("price near support")
    elif edge_position == EdgePosition.MID_RANGE:
        parts.append("price mid-range (wait for edge)")

    if breakout_risk == BreakoutRisk.HIGH:
        parts.append("breakout risk HIGH")
    elif breakout_risk == BreakoutRisk.MODERATE:
        parts.append("breakout risk moderate")

    if entry_quality is not None:
        if entry_quality >= 70:
            parts.append(f"entry quality strong ({entry_quality:.0f})")
        elif entry_quality <= 30:
            parts.append(f"entry not ideal ({entry_quality:.0f})")

    return "; ".join(parts)
