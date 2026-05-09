from range_scanner.config import ScannerConfig
from range_scanner.models import RangeStructure, Verdict
from range_scanner.scoring import (
    classify_verdict,
    compute_score,
    score_adx,
    score_atr_stability,
    score_containment,
    score_ema_slope,
    score_liquidity,
    score_range_width,
    score_reaction_strength,
    score_rotation,
    score_tightness,
    score_touches,
    score_trend_leakage,
)


class TestScoreLiquidity:
    def test_below_threshold(self):
        config = ScannerConfig()
        assert score_liquidity(10_000_000, config) == 0.0

    def test_at_threshold(self):
        config = ScannerConfig()
        assert score_liquidity(20_000_000, config) == 0.0

    def test_high_liquidity(self):
        config = ScannerConfig()
        assert score_liquidity(200_000_000, config) == 100.0


class TestScoreRangeWidth:
    def test_too_tight(self):
        assert score_range_width(1.0) < 30

    def test_sweet_spot(self):
        assert score_range_width(5.0) == 100.0

    def test_too_wide(self):
        assert score_range_width(13.0) < 25

    def test_extremely_wide(self):
        assert score_range_width(16.0) == 0.0


class TestScoreTouches:
    def test_zero_touches(self):
        assert score_touches(0) == 0.0

    def test_two_touches(self):
        assert score_touches(2) > 30

    def test_capped_benefit(self):
        s4 = score_touches(4)
        s10 = score_touches(10)
        assert s4 == s10


class TestScoreReactionStrength:
    def test_weak_reaction(self):
        assert score_reaction_strength(0.2) < 15

    def test_moderate_reaction(self):
        assert score_reaction_strength(1.0) >= 50

    def test_strong_reaction(self):
        assert score_reaction_strength(2.5) == 100.0


class TestScoreRotation:
    def test_zero_rotations(self):
        assert score_rotation(0) == 0.0

    def test_few_rotations(self):
        assert score_rotation(3) >= 40

    def test_many_rotations(self):
        assert score_rotation(8) == 100.0


class TestScoreTightness:
    def test_low_tightness(self):
        assert score_tightness(0.1) < 30

    def test_good_tightness(self):
        assert score_tightness(0.5) == 100.0


class TestScoreTrendLeakage:
    def test_no_leakage(self):
        assert score_trend_leakage(0.1) == 100.0

    def test_moderate_leakage(self):
        assert score_trend_leakage(0.4) < 60

    def test_high_leakage(self):
        assert score_trend_leakage(0.7) < 15


class TestScoreContainment:
    def test_high(self):
        assert score_containment(0.90) == 100.0

    def test_low(self):
        assert score_containment(0.4) < 35


class TestScoreADX:
    def test_low_adx(self):
        assert score_adx(15) == 100.0

    def test_high_adx(self):
        assert score_adx(40) < 10


class TestScoreEMASlope:
    def test_flat(self):
        assert score_ema_slope(1.0) == 100.0

    def test_steep(self):
        assert score_ema_slope(7.0) < 20


class TestScoreATR:
    def test_good_range(self):
        assert score_atr_stability(3.0) == 100.0

    def test_too_low(self):
        assert score_atr_stability(0.3) < 25

    def test_too_high(self):
        assert score_atr_stability(10.0) < 50


class TestComputeScore:
    def test_perfect_rotational_range(self):
        config = ScannerConfig()
        structure = RangeStructure(
            support=100.0, resistance=106.0, range_width_pct=6.0,
            support_touches=4, resistance_touches=4, containment_ratio=0.88,
            rotation_count=8, support_reaction_strength=2.0,
            resistance_reaction_strength=1.8, tightness=0.55, trend_leakage=0.1,
        )
        breakdown = compute_score(structure, adx=15.0, atr_pct=2.5, ema_slope_pct=0.5,
                                  avg_dollar_volume=200_000_000, config=config)
        assert breakdown.total >= 75

    def test_wide_lazy_range_penalized(self):
        config = ScannerConfig()
        structure = RangeStructure(
            support=100.0, resistance=115.0, range_width_pct=15.0,
            support_touches=4, resistance_touches=4, containment_ratio=0.90,
            rotation_count=2, support_reaction_strength=0.5,
            resistance_reaction_strength=0.4, tightness=0.2, trend_leakage=0.1,
        )
        breakdown = compute_score(structure, adx=15.0, atr_pct=2.5, ema_slope_pct=0.5,
                                  avg_dollar_volume=200_000_000, config=config)
        # Wide + low rotation + weak reactions should score significantly below a tight rotational range
        perfect = RangeStructure(
            support=100.0, resistance=106.0, range_width_pct=6.0,
            support_touches=4, resistance_touches=4, containment_ratio=0.88,
            rotation_count=8, support_reaction_strength=2.0,
            resistance_reaction_strength=1.8, tightness=0.55, trend_leakage=0.1,
        )
        perfect_breakdown = compute_score(perfect, adx=15.0, atr_pct=2.5, ema_slope_pct=0.5,
                                          avg_dollar_volume=200_000_000, config=config)
        assert breakdown.total < perfect_breakdown.total - 15

    def test_illiquid_penalty(self):
        config = ScannerConfig()
        structure = RangeStructure(
            support=100.0, resistance=106.0, range_width_pct=6.0,
            support_touches=4, resistance_touches=4, containment_ratio=0.85,
            rotation_count=6, support_reaction_strength=1.5,
            resistance_reaction_strength=1.5, tightness=0.5, trend_leakage=0.1,
        )
        breakdown = compute_score(structure, adx=15.0, atr_pct=2.5, ema_slope_pct=0.5,
                                  avg_dollar_volume=10_000_000, config=config)
        assert breakdown.liquidity_score == 0.0


class TestClassifyVerdict:
    def test_excellent(self):
        assert classify_verdict(80, adx=18, ema_slope_pct=1.0, trend_leakage=0.1) == Verdict.EXCELLENT_RANGE

    def test_trending_by_adx(self):
        assert classify_verdict(70, adx=35, ema_slope_pct=2.0, trend_leakage=0.1) == Verdict.TRENDING_NOT_RANGE

    def test_trending_by_leakage(self):
        assert classify_verdict(70, adx=22, ema_slope_pct=3.0, trend_leakage=0.6) == Verdict.TRENDING_NOT_RANGE

    def test_watchlist(self):
        assert classify_verdict(60, adx=22, ema_slope_pct=3.0, trend_leakage=0.2) == Verdict.WATCHLIST

    def test_messy(self):
        assert classify_verdict(40, adx=22, ema_slope_pct=3.0, trend_leakage=0.2) == Verdict.MESSY_RANGE
