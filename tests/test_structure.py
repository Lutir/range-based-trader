import numpy as np
import pandas as pd

from range_scanner.config import ScannerConfig
from range_scanner.structure import (
    cluster_prices,
    compute_containment_ratio,
    count_touches,
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
        prices = [100.0, 100.5, 101.0, 100.2]
        clusters = cluster_prices(prices, tolerance_pct=1.5)
        assert len(clusters) == 1

    def test_two_clusters(self):
        prices = [100.0, 100.5, 110.0, 110.5]
        clusters = cluster_prices(prices, tolerance_pct=1.5)
        assert len(clusters) == 2

    def test_empty(self):
        assert cluster_prices([], tolerance_pct=1.0) == []


class TestTouches:
    def test_support_touches(self):
        df = _make_range_df(support=100, resistance=110)
        touches = count_touches(df, zone=100.0, tolerance_pct=2.0, side="support")
        assert touches >= 1

    def test_resistance_touches(self):
        df = _make_range_df(support=100, resistance=110)
        touches = count_touches(df, zone=110.0, tolerance_pct=2.0, side="resistance")
        assert touches >= 1


class TestContainment:
    def test_high_containment(self):
        close = pd.Series(np.linspace(101, 109, 100))
        ratio = compute_containment_ratio(close, support=100, resistance=110)
        assert ratio == 1.0

    def test_low_containment(self):
        close = pd.Series(np.linspace(80, 130, 100))
        ratio = compute_containment_ratio(close, support=100, resistance=110)
        assert ratio < 0.5


class TestDetectRange:
    def test_clean_range_detected(self):
        df = _make_range_df()
        config = ScannerConfig()
        structure = detect_range_structure(df, config)
        assert structure is not None
        assert structure.support < structure.resistance
        assert structure.containment_ratio > 0.5

    def test_no_structure_for_trend(self):
        n = 120
        close = np.linspace(100, 160, n)
        high = close + 1
        low = close - 1
        volume = np.full(n, 5_000_000.0)
        df = pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": volume})
        config = ScannerConfig()
        structure = detect_range_structure(df, config)
        if structure is not None:
            assert structure.containment_ratio < 0.7
