import numpy as np
import pandas as pd

from range_scanner.indicators import compute_adx, compute_atr, compute_atr_pct, compute_compression_ratio, compute_ema, compute_ema_slope_pct, compute_gap_stats


def _make_flat_series(n: int = 100, base: float = 100.0, noise: float = 1.0) -> pd.DataFrame:
    np.random.seed(42)
    close = base + np.random.randn(n) * noise
    high = close + abs(np.random.randn(n) * noise * 0.5)
    low = close - abs(np.random.randn(n) * noise * 0.5)
    return pd.DataFrame({"high": high, "low": low, "close": close})


def _make_trending_series(n: int = 100, start: float = 100.0, end: float = 140.0) -> pd.DataFrame:
    close = np.linspace(start, end, n) + np.random.randn(n) * 0.5
    high = close + 1
    low = close - 1
    return pd.DataFrame({"high": high, "low": low, "close": close})


class TestATR:
    def test_atr_positive(self):
        df = _make_flat_series()
        atr = compute_atr(df["high"], df["low"], df["close"], period=14)
        assert atr.iloc[-1] > 0

    def test_atr_trending_larger(self):
        flat = _make_flat_series(noise=1.0)
        trend = _make_trending_series()
        atr_flat = compute_atr(flat["high"], flat["low"], flat["close"]).iloc[-1]
        atr_trend = compute_atr(trend["high"], trend["low"], trend["close"]).iloc[-1]
        assert atr_trend > atr_flat

    def test_atr_pct(self):
        df = _make_flat_series(base=200.0, noise=2.0)
        pct = compute_atr_pct(df["high"], df["low"], df["close"])
        assert pct is not None
        assert 0 < pct < 10


class TestADX:
    def test_flat_low_adx(self):
        df = _make_flat_series(n=150)
        adx = compute_adx(df["high"], df["low"], df["close"])
        assert adx.iloc[-1] < 30

    def test_trending_higher_adx(self):
        df = _make_trending_series(n=150)
        adx = compute_adx(df["high"], df["low"], df["close"])
        assert adx.iloc[-1] > 20


class TestEMA:
    def test_ema_length(self):
        df = _make_flat_series()
        ema = compute_ema(df["close"], period=20)
        assert len(ema) == len(df)

    def test_slope_flat(self):
        df = _make_flat_series(n=100, noise=0.1)
        slope = compute_ema_slope_pct(df["close"], period=20, slope_window=20)
        assert slope is not None
        assert abs(slope) < 2.0

    def test_slope_trending(self):
        df = _make_trending_series(n=100)
        slope = compute_ema_slope_pct(df["close"], period=20, slope_window=20)
        assert slope is not None
        assert slope > 5.0


class TestCompression:
    def test_normal_volatility(self):
        df = _make_flat_series(n=100, noise=1.0)
        ratio, label = compute_compression_ratio(df["high"], df["low"], df["close"])
        assert 0.5 < ratio < 1.5
        assert label in ("NORMAL", "COMPRESSING", "EXPANDING")

    def test_compressing(self):
        np.random.seed(10)
        n = 60
        close = np.full(n, 100.0)
        noise = np.concatenate([np.random.randn(40) * 3, np.random.randn(20) * 0.3])
        close = close + noise
        high = close + abs(np.concatenate([np.random.randn(40) * 2, np.random.randn(20) * 0.2]))
        low = close - abs(np.concatenate([np.random.randn(40) * 2, np.random.randn(20) * 0.2]))
        ratio, label = compute_compression_ratio(pd.Series(high), pd.Series(low), pd.Series(close))
        assert ratio < 0.8
        assert label == "COMPRESSING"


class TestGapStats:
    def test_no_gaps(self):
        close = pd.Series([100.0] * 50)
        open_prices = pd.Series([100.0] * 50)
        freq, avg, mx = compute_gap_stats(open_prices, close)
        assert freq == 0.0
        assert avg == 0.0

    def test_all_large_gaps(self):
        close = pd.Series([100.0] * 50)
        open_prices = pd.Series([103.0] * 50)
        freq, avg, mx = compute_gap_stats(open_prices, close)
        assert freq > 0.9
        assert avg > 2.5

    def test_mixed_gaps(self):
        np.random.seed(99)
        close = pd.Series(np.full(100, 100.0))
        opens = close.copy()
        opens.iloc[10] = 103.0
        opens.iloc[30] = 97.0
        opens.iloc[50] = 104.0
        freq, avg, mx = compute_gap_stats(opens, close, threshold_pct=2.0)
        assert 0.01 < freq < 0.10
        assert mx >= 3.0
