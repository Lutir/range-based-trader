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
    score_touches,
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
        assert score_range_width(1.0) < 40

    def test_good_range(self):
        assert score_range_width(7.0) == 100.0

    def test_too_wide(self):
        assert score_range_width(16.0) < 20


class TestScoreTouches:
    def test_zero_touches(self):
        assert score_touches(0) == 0.0

    def test_two_touches(self):
        assert score_touches(2) > 40

    def test_capped_benefit(self):
        s4 = score_touches(4)
        s10 = score_touches(10)
        assert s4 == s10


class TestScoreContainment:
    def test_high(self):
        assert score_containment(0.85) == 100.0

    def test_low(self):
        assert score_containment(0.4) < 40


class TestScoreADX:
    def test_low_adx(self):
        assert score_adx(15) == 100.0

    def test_high_adx(self):
        assert score_adx(40) < 20


class TestScoreEMASlope:
    def test_flat(self):
        assert score_ema_slope(1.0) == 100.0

    def test_steep(self):
        assert score_ema_slope(7.0) < 30


class TestScoreATR:
    def test_good_range(self):
        assert score_atr_stability(3.0) == 100.0

    def test_too_low(self):
        assert score_atr_stability(0.3) < 30

    def test_too_high(self):
        assert score_atr_stability(10.0) < 50


class TestComputeScore:
    def test_perfect_range(self):
        config = ScannerConfig()
        structure = RangeStructure(
            support=100.0, resistance=107.0, range_width_pct=7.0,
            support_touches=4, resistance_touches=4, containment_ratio=0.85,
        )
        breakdown = compute_score(structure, adx=15.0, atr_pct=2.5, ema_slope_pct=0.5,
                                  avg_dollar_volume=200_000_000, config=config)
        assert breakdown.total >= 80

    def test_illiquid_penalty(self):
        config = ScannerConfig()
        structure = RangeStructure(
            support=100.0, resistance=107.0, range_width_pct=7.0,
            support_touches=4, resistance_touches=4, containment_ratio=0.85,
        )
        breakdown = compute_score(structure, adx=15.0, atr_pct=2.5, ema_slope_pct=0.5,
                                  avg_dollar_volume=10_000_000, config=config)
        assert breakdown.liquidity_score == 0.0


class TestClassifyVerdict:
    def test_excellent(self):
        assert classify_verdict(85, adx=18, ema_slope_pct=1.0) == Verdict.EXCELLENT_RANGE

    def test_trending(self):
        assert classify_verdict(70, adx=35, ema_slope_pct=2.0) == Verdict.TRENDING_NOT_RANGE

    def test_watchlist(self):
        assert classify_verdict(70, adx=22, ema_slope_pct=3.0) == Verdict.WATCHLIST

    def test_messy(self):
        assert classify_verdict(50, adx=22, ema_slope_pct=3.0) == Verdict.MESSY_RANGE
