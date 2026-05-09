from enum import Enum
from pydantic import BaseModel


class Verdict(str, Enum):
    EXCELLENT_RANGE = "EXCELLENT_RANGE"
    WATCHLIST = "WATCHLIST"
    MESSY_RANGE = "MESSY_RANGE"
    TRENDING_NOT_RANGE = "TRENDING_NOT_RANGE"
    ILLIQUID = "ILLIQUID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"


class RangeStructure(BaseModel):
    support: float
    resistance: float
    range_width_pct: float
    support_touches: int
    resistance_touches: int
    containment_ratio: float


class ScoreBreakdown(BaseModel):
    liquidity_score: float
    range_width_score: float
    support_touch_score: float
    resistance_touch_score: float
    containment_score: float
    adx_score: float
    ema_slope_score: float
    atr_stability_score: float
    total: float


class TickerScanResult(BaseModel):
    ticker: str
    score: float = 0.0
    verdict: Verdict = Verdict.ERROR
    support: float | None = None
    resistance: float | None = None
    range_width_pct: float | None = None
    support_touches: int | None = None
    resistance_touches: int | None = None
    containment_ratio: float | None = None
    adx_14: float | None = None
    atr_pct: float | None = None
    ema20_slope_pct: float | None = None
    avg_volume_20: float | None = None
    avg_dollar_volume_20: float | None = None
    latest_close: float | None = None
    risk_note: str = ""
    skip_reason: str = ""
