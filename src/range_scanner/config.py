from pydantic import BaseModel


class ScannerConfig(BaseModel):
    lookback: int = 120
    min_candles: int = 80
    min_volume: int = 1_000_000
    min_dollar_volume: int = 20_000_000
    pivot_window: int = 3
    atr_period: int = 14
    adx_period: int = 14
    ema_period: int = 20
    ema_slope_window: int = 20
    volume_avg_window: int = 20
    zone_tolerance_atr_mult: float = 0.75
    zone_tolerance_min_pct: float = 1.0
    touch_max_benefit: int = 4
    top: int = 20
