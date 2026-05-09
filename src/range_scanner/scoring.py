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
    if range_width_pct < 2:
        return _clamp(range_width_pct / 2 * 40)
    if range_width_pct <= 4:
        return _clamp(40 + (range_width_pct - 2) / 2 * 30)
    if range_width_pct <= 10:
        return 100.0
    if range_width_pct <= 15:
        return _clamp(100 - (range_width_pct - 10) / 5 * 60)
    return 10.0


def score_touches(touches: int, max_benefit: int = 4) -> float:
    if touches < 2:
        return _clamp(touches * 25)
    effective = min(touches, max_benefit)
    return _clamp(25 + (effective - 1) / (max_benefit - 1) * 75)


def score_containment(containment_ratio: float) -> float:
    if containment_ratio >= 0.80:
        return 100.0
    if containment_ratio >= 0.65:
        return _clamp(50 + (containment_ratio - 0.65) / 0.15 * 50)
    return _clamp(containment_ratio / 0.65 * 50)


def score_adx(adx: float) -> float:
    if adx < 20:
        return 100.0
    if adx <= 25:
        return _clamp(100 - (adx - 20) / 5 * 30)
    if adx <= 35:
        return _clamp(70 - (adx - 25) / 10 * 50)
    return _clamp(20 - (adx - 35) / 10 * 20)


def score_ema_slope(abs_slope_pct: float) -> float:
    if abs_slope_pct < 2:
        return 100.0
    if abs_slope_pct <= 5:
        return _clamp(100 - (abs_slope_pct - 2) / 3 * 60)
    return _clamp(40 - (abs_slope_pct - 5) / 5 * 30)


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
    cont = score_containment(structure.containment_ratio)
    adx_s = score_adx(adx)
    ema_s = score_ema_slope(abs(ema_slope_pct))
    atr_s = score_atr_stability(atr_pct)

    total = (
        liq * config.weight_liquidity / 100
        + rw * config.weight_range_width / 100
        + st * config.weight_support_touches / 100
        + rt * config.weight_resistance_touches / 100
        + cont * config.weight_containment / 100
        + adx_s * config.weight_adx / 100
        + ema_s * config.weight_ema_slope / 100
        + atr_s * config.weight_atr_stability / 100
    )
    total = _clamp(total)

    return ScoreBreakdown(
        liquidity_score=round(liq, 2),
        range_width_score=round(rw, 2),
        support_touch_score=round(st, 2),
        resistance_touch_score=round(rt, 2),
        containment_score=round(cont, 2),
        adx_score=round(adx_s, 2),
        ema_slope_score=round(ema_s, 2),
        atr_stability_score=round(atr_s, 2),
        total=round(total, 2),
    )


def classify_verdict(score: float, adx: float, ema_slope_pct: float) -> Verdict:
    if adx > 30 or abs(ema_slope_pct) > 6:
        return Verdict.TRENDING_NOT_RANGE
    if score >= 80 and adx < 25:
        return Verdict.EXCELLENT_RANGE
    if score >= 65:
        return Verdict.WATCHLIST
    if score >= 45:
        return Verdict.MESSY_RANGE
    return Verdict.MESSY_RANGE
