import numpy as np
import pandas as pd

from range_scanner.config import ScannerConfig
from range_scanner.structure import (
    cluster_prices_weighted,
    compute_containment_ratio,
    compute_range_tightness,
    compute_rotation_count,
    count_touches_with_strength,
    detect_higher_highs_lows,
    detect_range_structure,
    find_pivot_highs,
    find_pivot_lows,
)


def _make_range_df(n: int = 120, support: float = 100.0, resistance: float = 110.0) -> pd.DataFrame:
    np.random.seed(7)
    mid = (support + resistance) / 2
    amplitude = (resistance - support) / 2
    t = np.linspace(0, 8 * np.pi, n)
    close = mid + amplitude * 0.8 * np.sin(t) + np.random.randn(n) * 0.5
    close = np.clip(close, support - 1, resistance + 1)
    high = close + abs(np.random.randn(n) * 0.5)
    low = close - abs(np.random.randn(n) * 0.5)
    volume = np.full(n, 5_000_000.0)
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume})


def _make_tight_range_df(n: int = 120, support: float = 100.0, resistance: float = 106.0) -> pd.DataFrame:
    """Tight oscillating range — the ideal structure."""
    np.random.seed(42)
    mid = (support + resistance) / 2
    amplitude = (resistance - support) / 2
    t = np.linspace(0, 12 * np.pi, n)
    close = mid + amplitude * 0.85 * np.sin(t) + np.random.randn(n) * 0.3
    close = np.clip(close, support - 0.5, resistance + 0.5)
    high = close + abs(np.random.randn(n) * 0.4)
    low = close - abs(np.random.randn(n) * 0.4)
    volume = np.full(n, 5_000_000.0)
    return pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume})


class TestPivots:
    def test_finds_pivot_highs(self):
        df = _make_range_df()
        pivots = find_pivot_highs(df["high"], window=3)
        assert len(pivots) >= 2

    def test_finds_pivot_lows(self):
        df = _make_range_df()
        pivots = find_pivot_lows(df["low"], window=3)
        assert len(pivots) >= 2


class TestClustering:
    def test_single_cluster(self):
        pivots = [(10, 100.0), (20, 100.5), (30, 101.0), (40, 100.2)]
        clusters = cluster_prices_weighted(pivots, tolerance_pct=1.5, total_bars=120)
        assert len(clusters) == 1

    def test_two_clusters(self):
        pivots = [(10, 100.0), (20, 100.5), (30, 110.0), (40, 110.5)]
        clusters = cluster_prices_weighted(pivots, tolerance_pct=1.5, total_bars=120)
        assert len(clusters) == 2

    def test_empty(self):
        assert cluster_prices_weighted([], tolerance_pct=1.0, total_bars=120) == []


class TestTouches:
    def test_support_touches(self):
        df = _make_range_df(support=100, resistance=110)
        touches, strength = count_touches_with_strength(df, zone=100.0, tolerance_pct=2.0, side="support")
        assert touches >= 1
        assert strength >= 0

    def test_resistance_touches(self):
        df = _make_range_df(support=100, resistance=110)
        touches, strength = count_touches_with_strength(df, zone=110.0, tolerance_pct=2.0, side="resistance")
        assert touches >= 1
        assert strength >= 0


class TestContainment:
    def test_high_containment(self):
        close = pd.Series(np.linspace(101, 109, 100))
        ratio = compute_containment_ratio(close, support=100, resistance=110)
        assert ratio == 1.0

    def test_low_containment(self):
        close = pd.Series(np.linspace(80, 130, 100))
        ratio = compute_containment_ratio(close, support=100, resistance=110)
        assert ratio < 0.5


class TestRotation:
    def test_oscillating_has_rotations(self):
        t = np.linspace(0, 8 * np.pi, 120)
        close = pd.Series(105 + 4 * np.sin(t))
        rotations = compute_rotation_count(close, support=100, resistance=110)
        assert rotations >= 6

    def test_flat_midpoint_no_rotations(self):
        close = pd.Series(np.full(100, 105.0))
        rotations = compute_rotation_count(close, support=100, resistance=110)
        assert rotations == 0

    def test_trending_few_rotations(self):
        close = pd.Series(np.linspace(100, 130, 120))
        rotations = compute_rotation_count(close, support=100, resistance=110)
        assert rotations <= 2


class TestTightness:
    def test_tight_oscillation(self):
        t = np.linspace(0, 6 * np.pi, 100)
        close = pd.Series(105 + 4.5 * np.sin(t))
        tightness = compute_range_tightness(close, support=100, resistance=110)
        assert tightness > 0.4

    def test_clustered_at_midpoint(self):
        close = pd.Series(np.full(100, 105.0) + np.random.randn(100) * 0.1)
        tightness = compute_range_tightness(close, support=100, resistance=110)
        assert tightness < 0.1


class TestTrendLeakage:
    def test_flat_pivots_low_leakage(self):
        highs = [(i * 10, 110.0 + np.random.randn() * 0.5) for i in range(10)]
        lows = [(i * 10 + 5, 100.0 + np.random.randn() * 0.5) for i in range(10)]
        leakage = detect_higher_highs_lows(highs, lows)
        assert leakage < 0.5

    def test_uptrend_high_leakage(self):
        highs = [(i * 10, 110.0 + i * 2) for i in range(10)]
        lows = [(i * 10 + 5, 100.0 + i * 2) for i in range(10)]
        leakage = detect_higher_highs_lows(highs, lows)
        assert leakage > 0.7


class TestDetectRange:
    def test_clean_range_detected(self):
        df = _make_range_df()
        config = ScannerConfig()
        structure = detect_range_structure(df, config)
        assert structure is not None
        assert structure.support < structure.resistance
        assert structure.containment_ratio > 0.5
        assert structure.rotation_count >= 1

    def test_tight_range_good_metrics(self):
        df = _make_tight_range_df()
        config = ScannerConfig()
        structure = detect_range_structure(df, config)
        assert structure is not None
        assert structure.rotation_count >= 4
        assert structure.tightness > 0.3

    def test_trend_has_leakage(self):
        n = 120
        close = np.linspace(100, 140, n) + np.random.randn(n) * 0.5
        high = close + 1
        low = close - 1
        volume = np.full(n, 5_000_000.0)
        df = pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume})
        config = ScannerConfig()
        structure = detect_range_structure(df, config)
        if structure is not None:
            assert structure.trend_leakage > 0.3
