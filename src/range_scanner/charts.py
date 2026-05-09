from pathlib import Path

import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd

from range_scanner.models import TickerScanResult


def export_chart(
    df: pd.DataFrame, result: TickerScanResult, rank: int, output_dir: Path
) -> Path:
    """Generate a PNG chart with support/resistance zones and metadata."""
    output_dir.mkdir(parents=True, exist_ok=True)

    ohlc = df[["open", "high", "low", "close", "volume"]].copy()
    ohlc.index = pd.to_datetime(df["timestamp"])
    ohlc.index.name = "Date"

    support = result.support
    resistance = result.resistance
    midpoint = (support + resistance) / 2 if support and resistance else None

    addplots = []

    if support and resistance:
        n = len(ohlc)
        sup_line = pd.Series([support] * n, index=ohlc.index)
        res_line = pd.Series([resistance] * n, index=ohlc.index)
        mid_line = pd.Series([midpoint] * n, index=ohlc.index)

        addplots.append(mpf.make_addplot(sup_line, color="green", linestyle="--", width=1.5))
        addplots.append(mpf.make_addplot(res_line, color="red", linestyle="--", width=1.5))
        addplots.append(mpf.make_addplot(mid_line, color="gray", linestyle=":", width=0.8))

    title_line1 = f"{result.ticker} | {result.verdict.value} | Score {result.score:.0f}"
    title_line2 = ""
    if support and resistance:
        width_str = f"{result.range_width_pct:.1f}%" if result.range_width_pct else "?"
        rot_str = str(result.rotation_count) if result.rotation_count is not None else "?"
        title_line2 = f"Range: {support:.1f}–{resistance:.1f} | Width: {width_str} | Rotations: {rot_str}"

    sub_str = ""
    if result.structure_score is not None:
        sub_str = f"Str: {result.structure_score:.0f} | Reg: {result.regime_score:.0f} | Liq: {result.liquidity_score:.0f}"

    full_title = f"{title_line1}\n{title_line2}\n{sub_str}"

    filename = f"{rank:02d}_{result.ticker}_{result.verdict.value}_{result.score:.0f}.png"
    filepath = output_dir / filename

    style = mpf.make_mpf_style(
        base_mpf_style="charles",
        gridstyle=":",
        gridcolor="#e0e0e0",
    )

    fig, axes = mpf.plot(
        ohlc,
        type="candle",
        style=style,
        title=full_title,
        volume=True,
        addplot=addplots if addplots else None,
        figsize=(14, 8),
        returnfig=True,
        tight_layout=True,
    )

    # Add reason as text at bottom
    if result.reason:
        reason_text = result.reason[:120]
        fig.text(0.5, 0.01, reason_text, ha="center", fontsize=8, color="gray")

    fig.savefig(filepath, dpi=100, bbox_inches="tight")
    plt.close(fig)

    return filepath
