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
    """Tighter sweet spot: 3-8% is ideal. Heavily penalize >12%."""
    if range_width_pct < 2:
        return _clamp(range_width_pct / 2 * 30)
    if range_width_pct <= 3:
        return _clamp(30 + (range_width_pct - 2) * 40)
    if range_width_pct <= 8:
        return 100.0
    if range_width_pct <= 12:
        return _clamp(100 - (range_width_pct - 8) / 4 * 70)
    if range_width_pct <= 15:
        return _clamp(30 - (range_width_pct - 12) / 3 * 25)
    return 0.0


def score_touches(touches: int, max_benefit: int = 4) -> float:
    if touches < 2:
        return _clamp(touches * 20)
    effective = min(touches, max_benefit)
    return _clamp(20 + (effective - 1) / (max_benefit - 1) * 80)


def score_reaction_strength(avg_reaction_pct: float) -> float:
    """Reward strong reactions (sharp reversals), penalize weak lazy touches."""
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
    """Reward actual oscillations between zones. This is the key differentiator."""
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
    """Reward range utilization — closes should use the full range, not cluster at midpoint."""
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
    """Penalize sequential higher-highs/higher-lows pattern."""
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

    # New weight distribution prioritizing rotational structure
    # Rotation + reaction strength = 30% (the core "is this a real range?" signal)
    # Structure quality = 25% (containment + tightness + range width)
    # Anti-trend = 20% (ADX + EMA slope + trend leakage)
    # Touches = 15% (with reaction quality baked in)
    # Liquidity + ATR = 10% (filter, not differentiator)
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


def classify_verdict(score: float, adx: float, ema_slope_pct: float, trend_leakage: float) -> Verdict:
    if adx > 30 or abs(ema_slope_pct) > 6 or trend_leakage > 0.5:
        return Verdict.TRENDING_NOT_RANGE
    if score >= 75 and adx < 25:
        return Verdict.EXCELLENT_RANGE
    if score >= 55:
        return Verdict.WATCHLIST
    if score >= 35:
        return Verdict.MESSY_RANGE
    return Verdict.MESSY_RANGE
