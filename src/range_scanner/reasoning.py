"""
AI-style reasoning generator for stock analysis.

Turns raw metrics into readable, contextual narratives that explain
WHY the scanner made its decision and WHAT it means practically.

Instead of:
  "7 rotations (strong); width 8.1%; price near resistance; ADX 18"

You get:
  "ADSK shows a well-defined range between $229 and $247 (8.1% width)
   that has been actively rotating for several months. Price has bounced
   between these levels 7 times, confirming both zones. However, price
   is currently pressing against resistance at $247. In a risk-on market
   with the tech sector trending up, this looks more like a breakout
   setup than a mean-reversion short. Wait for either a confirmed
   rejection at resistance or a clean breakout above $250 before acting."

This is template-based (no external API needed) but designed to read
like thoughtful analysis, not mechanical output.
"""

from range_scanner.models import (
    TickerScanResult, Verdict, EdgePosition, BreakoutRisk, SetupType,
)


def generate_narrative(result: TickerScanResult) -> str:
    """Generate a full narrative analysis for a ticker scan result.

    Combines all metrics into 3-5 sentences of readable reasoning
    that explains the situation like a knowledgeable analyst would.
    """
    if result.skip_reason:
        return _skipped_narrative(result)

    parts = []
    parts.append(_structure_sentence(result))
    parts.append(_position_sentence(result))
    parts.append(_risk_sentence(result))
    parts.append(_action_sentence(result))

    return " ".join(p for p in parts if p)


def _skipped_narrative(result: TickerScanResult) -> str:
    """Narrative for skipped/failed tickers."""
    if result.verdict == Verdict.INSUFFICIENT_DATA:
        return f"{result.ticker} doesn't have enough trading history to analyze. Need at least 80 days of data to detect meaningful structure."

    if result.verdict == Verdict.ILLIQUID:
        return f"{result.ticker} doesn't trade enough volume to be useful for range trading. Low liquidity means wide spreads and difficulty entering/exiting positions."

    if result.verdict == Verdict.ERROR:
        return f"{result.ticker} encountered an error during analysis: {result.skip_reason}"

    if "No clear range" in (result.skip_reason or ""):
        return f"{result.ticker} doesn't show a clear range structure. Price action is too chaotic or directional to identify reliable support and resistance zones."

    return f"{result.ticker} was skipped: {result.skip_reason}"


def _structure_sentence(result: TickerScanResult) -> str:
    """Describe the range structure quality."""
    ticker = result.ticker

    if result.verdict in (Verdict.BROKEN_UP, Verdict.BROKEN_DOWN):
        direction = "above resistance" if result.verdict == Verdict.BROKEN_UP else "below support"
        return (f"{ticker} had a defined range between ${result.support:.0f} and ${result.resistance:.0f}, "
                f"but price has since broken {direction} at ${result.latest_close:.2f}. "
                f"The previous range is no longer active.")

    if result.verdict == Verdict.TRENDING_NOT_RANGE:
        return (f"{ticker} is currently trending rather than range-bound. "
                f"Despite detecting some boundaries (${result.support:.0f}–${result.resistance:.0f}), "
                f"the directional momentum is too strong for reliable range trading.")

    # Active range
    rot = result.rotation_count or 0
    width = result.range_width_pct or 0

    if rot >= 7:
        rot_desc = f"Price has rotated between these levels {rot} times — a heavily tested, mature range"
    elif rot >= 4:
        rot_desc = f"With {rot} confirmed rotations, this is a well-established range"
    else:
        rot_desc = f"The range shows {rot} rotations, which is adequate but not deeply tested"

    if width <= 5:
        width_desc = "tight"
    elif width <= 10:
        width_desc = "well-sized"
    elif width <= 15:
        width_desc = "somewhat wide"
    else:
        width_desc = "very wide"

    score = result.score
    if score >= 75:
        quality = "This is a high-quality range structure"
    elif score >= 55:
        quality = "This is a reasonable range structure"
    else:
        quality = "This is a weak range structure"

    return (f"{quality}. {ticker} is trading in a {width_desc} range between "
            f"${result.support:.0f} and ${result.resistance:.0f} "
            f"({width:.1f}% width). {rot_desc}.")


def _position_sentence(result: TickerScanResult) -> str:
    """Describe where price is NOW within the range."""
    if result.verdict in (Verdict.BROKEN_UP, Verdict.BROKEN_DOWN, Verdict.TRENDING_NOT_RANGE):
        return ""

    edge = result.edge_position
    entry = result.entry_quality or 0
    pos = result.position_in_range or 0.5

    if edge == EdgePosition.NEAR_SUPPORT:
        pos_desc = (f"Price is currently near support at ${result.support:.0f} "
                    f"(position: {pos:.0%} of range).")
        if entry >= 60:
            pos_desc += " This is a potentially actionable long entry area."
        else:
            pos_desc += " However, conditions aren't ideal for entry yet."

    elif edge == EdgePosition.NEAR_RESISTANCE:
        pos_desc = (f"Price is pressing against resistance at ${result.resistance:.0f} "
                    f"(position: {pos:.0%} of range).")
        if result.breakout_risk == BreakoutRisk.HIGH:
            pos_desc += " With elevated volume and upward momentum, this looks more like a breakout attempt than a reversal point."
        else:
            pos_desc += " Watch for either a clean rejection back into the range or a confirmed break above."

    elif edge == EdgePosition.MID_RANGE:
        pos_desc = (f"Price is sitting mid-range at ${result.latest_close:.2f} "
                    f"(position: {pos:.0%}). "
                    f"This is a 'no man's land' — too far from either edge to be actionable. "
                    f"Best to wait for price to approach support or resistance before considering a trade.")

    elif edge == EdgePosition.UPPER_HALF:
        pos_desc = (f"Price is in the upper half of the range at ${result.latest_close:.2f} "
                    f"(position: {pos:.0%}). Closer to resistance than support, "
                    f"but not quite at the edge yet.")

    elif edge == EdgePosition.LOWER_HALF:
        pos_desc = (f"Price is in the lower half of the range at ${result.latest_close:.2f} "
                    f"(position: {pos:.0%}). Getting closer to support, "
                    f"which could become interesting if it reaches the zone.")

    else:
        pos_desc = ""

    return pos_desc


def _risk_sentence(result: TickerScanResult) -> str:
    """Describe risk factors."""
    if result.verdict in (Verdict.BROKEN_UP, Verdict.BROKEN_DOWN, Verdict.TRENDING_NOT_RANGE):
        return ""

    risks = []

    # Gap risk
    gap_freq = result.gap_frequency or 0
    if gap_freq > 0.15:
        risks.append(f"this stock gaps frequently ({gap_freq:.0%} of days have >2% overnight gaps), making support/resistance less reliable")
    elif gap_freq > 0.08:
        risks.append(f"moderate gap risk ({gap_freq:.0%} of days)")

    # Compression
    if result.compression_label == "COMPRESSING":
        if result.edge_position == EdgePosition.NEAR_RESISTANCE:
            risks.append("volatility is compressing near resistance — this often precedes a breakout")
        elif result.edge_position == EdgePosition.NEAR_SUPPORT:
            risks.append("volatility is compressing near support — watch for a breakdown")
        else:
            risks.append("volatility is compressing (coiling), which often precedes a large move")
    elif result.compression_label == "EXPANDING":
        risks.append("volatility is expanding, making the range less stable")

    # Earnings
    if result.earnings_risk == "HIGH":
        risks.append(f"earnings are in {result.days_to_earnings} days — avoid range-trading assumptions until after the report")
    elif result.earnings_risk == "MODERATE":
        risks.append(f"earnings are coming up in {result.days_to_earnings} days — be cautious with position sizing")

    # Short interest
    if result.short_interest_risk == "HIGH":
        si = result.short_pct_float or 0
        risks.append(f"high short interest ({si:.0f}% of float) creates squeeze risk near resistance and volatile behavior")
    elif result.short_interest_risk == "MODERATE":
        si = result.short_pct_float or 0
        risks.append(f"elevated short interest ({si:.0f}% of float)")

    if not risks:
        return "No significant risk flags detected."

    if len(risks) == 1:
        return f"Key risk: {risks[0]}."
    else:
        return "Risks to consider: " + "; ".join(risks) + "."


def _action_sentence(result: TickerScanResult) -> str:
    """What should the reader DO with this information?"""
    if result.verdict == Verdict.BROKEN_UP:
        return "This is no longer a range trade. The prior structure has been invalidated by the breakout."

    if result.verdict == Verdict.BROKEN_DOWN:
        return "This is no longer a range trade. Support has failed and the prior range is broken."

    if result.verdict == Verdict.TRENDING_NOT_RANGE:
        return "Not suitable for range trading. Look for trend-following setups instead, or wait for the trend to exhaust and a new range to form."

    if result.verdict == Verdict.TOO_WIDE:
        return "The range is too wide to trade effectively. The distance between support and resistance makes risk/reward poor for mean-reversion entries."

    setup = result.setup_type

    if setup == SetupType.MEAN_REVERSION_LONG:
        return (f"Setup: potential long near support. Look for a bullish candle pattern "
                f"or volume confirmation near ${result.support:.0f} before entering. "
                f"Target midpoint or resistance. Stop below support.")

    if setup == SetupType.MEAN_REVERSION_SHORT:
        return (f"Setup: potential short near resistance. Look for a bearish rejection "
                f"or failed breakout near ${result.resistance:.0f}. "
                f"Target midpoint or support. Stop above resistance.")

    if setup == SetupType.BREAKOUT_WATCH_UPSIDE:
        return (f"Setup: breakout watch. Rather than shorting resistance, watch for a "
                f"confirmed break above ${result.resistance:.0f} with volume. "
                f"If it fails and closes back inside, that becomes a strong short signal.")

    if setup == SetupType.BREAKDOWN_WATCH_DOWNSIDE:
        return (f"Setup: breakdown watch. Support at ${result.support:.0f} is under pressure. "
                f"If it breaks with volume, the range is over. "
                f"If it holds and bounces, that's a validated long entry.")

    if setup == SetupType.AVOID_CONTEXT_CONFLICT:
        return ("The chart structure looks range-like, but broader context conflicts with the setup. "
                "The market or sector environment doesn't support this trade right now. Monitor only.")

    # RANGE_MONITOR_ONLY or no setup
    return ("Add to watchlist. The range is valid but price isn't at an actionable edge right now. "
            "Set alerts near support and resistance to catch the next opportunity.")
