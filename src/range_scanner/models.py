from enum import Enum
from pydantic import BaseModel


class Verdict(str, Enum):
    EXCELLENT_RANGE = "EXCELLENT_RANGE"
    RANGE_PRESSING_RESISTANCE = "RANGE_PRESSING_RESISTANCE"
    RANGE_PRESSING_SUPPORT = "RANGE_PRESSING_SUPPORT"
    WATCHLIST = "WATCHLIST"
    WIDE_RANGE = "WIDE_RANGE"
    MESSY_RANGE = "MESSY_RANGE"
    BROKEN_UP = "BROKEN_UP"
    BROKEN_DOWN = "BROKEN_DOWN"
    TOO_WIDE = "TOO_WIDE"
    TRENDING_NOT_RANGE = "TRENDING_NOT_RANGE"
    ILLIQUID = "ILLIQUID"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"


class EdgePosition(str, Enum):
    NEAR_SUPPORT = "NEAR_SUPPORT"
    LOWER_HALF = "LOWER_HALF"
    MID_RANGE = "MID_RANGE"
    UPPER_HALF = "UPPER_HALF"
    NEAR_RESISTANCE = "NEAR_RESISTANCE"
    BROKEN_UP = "BROKEN_UP"
    BROKEN_DOWN = "BROKEN_DOWN"


class BreakoutRisk(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    NA = "N/A"


class SetupType(str, Enum):
    MEAN_REVERSION_LONG = "MEAN_REVERSION_LONG"
    MEAN_REVERSION_SHORT = "MEAN_REVERSION_SHORT"
    BREAKOUT_WATCH_UPSIDE = "BREAKOUT_WATCH_UPSIDE"
    BREAKDOWN_WATCH_DOWNSIDE = "BREAKDOWN_WATCH_DOWNSIDE"
    RANGE_MONITOR_ONLY = "RANGE_MONITOR_ONLY"
    AVOID_CONTEXT_CONFLICT = "AVOID_CONTEXT_CONFLICT"
    NOT_RANGE_TRADE = "NOT_RANGE_TRADE"


class RangeStructure(BaseModel):
    support: float
    resistance: float
    range_width_pct: float
    support_touches: int
    resistance_touches: int
    containment_ratio: float
    rotation_count: int = 0
    support_reaction_strength: float = 0.0
    resistance_reaction_strength: float = 0.0
    tightness: float = 0.0
    trend_leakage: float = 0.0
    resistance_false_breaks: int = 0
    support_false_breaks: int = 0


class ScoreBreakdown(BaseModel):
    liquidity_score: float
    range_width_score: float
    support_touch_score: float
    resistance_touch_score: float
    containment_score: float
    rotation_score: float
    reaction_score: float
    tightness_score: float
    adx_score: float
    ema_slope_score: float
    trend_leakage_score: float
    atr_stability_score: float
    total: float


class TickerScanResult(BaseModel):
    ticker: str
    score: float = 0.0
    verdict: Verdict = Verdict.ERROR
    # Setup classification
    setup_type: SetupType = SetupType.NOT_RANGE_TRADE
    context_score: float | None = None
    # Range state
    entry_quality: float | None = None
    position_in_range: float | None = None
    edge_position: EdgePosition | None = None
    breakout_risk: BreakoutRisk = BreakoutRisk.NA
    # Structure
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
    rotation_count: int | None = None
    tightness: float | None = None
    trend_leakage: float | None = None
    gap_frequency: float | None = None
    avg_gap_pct: float | None = None
    compression_ratio: float | None = None
    compression_label: str | None = None
    days_to_earnings: int | None = None
    earnings_risk: str | None = None
    # Sub-scores for explainability
    structure_score: float | None = None
    regime_score: float | None = None
    liquidity_score: float | None = None
    data_start: str | None = None
    data_end: str | None = None
    risk_note: str = ""
    reason: str = ""
    skip_reason: str = ""
