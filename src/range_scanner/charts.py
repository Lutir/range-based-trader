from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import mplfinance as mpf
import numpy as np
import pandas as pd

from range_scanner.models import TickerScanResult

# Japandi palette — muted earth tones, high contrast on warm neutrals
_BG = "#FAF8F5"
_PANEL_BG = "#FAF8F5"
_TEXT = "#2D2A26"
_TEXT_MUTED = "#7A756E"
_GRID = "#E8E4DF"
_CANDLE_UP = "#5B8A72"
_CANDLE_DOWN = "#C27D5E"
_VOLUME_UP = "#5B8A7244"
_VOLUME_DOWN = "#C27D5E44"
_SUPPORT = "#5B8A72"
_RESISTANCE = "#C27D5E"
_MIDPOINT = "#B8B2A8"
_ZONE_ALPHA = 0.08

_JAPANDI_STYLE = mpf.make_mpf_style(
    base_mpf_style="charles",
    marketcolors=mpf.make_marketcolors(
        up=_CANDLE_UP,
        down=_CANDLE_DOWN,
        edge={"up": _CANDLE_UP, "down": _CANDLE_DOWN},
        wick={"up": _CANDLE_UP, "down": _CANDLE_DOWN},
        volume={"up": _VOLUME_UP, "down": _VOLUME_DOWN},
    ),
    facecolor=_BG,
    edgecolor=_BG,
    figcolor=_BG,
    gridcolor=_GRID,
    gridstyle="-",
    gridaxis="horizontal",
    y_on_right=True,
    rc={
        "axes.labelcolor": _TEXT_MUTED,
        "xtick.color": _TEXT_MUTED,
        "ytick.color": _TEXT_MUTED,
        "font.size": 9,
    },
)


def export_chart(
    df: pd.DataFrame, result: TickerScanResult, rank: int, output_dir: Path
) -> Path:
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

        addplots.append(mpf.make_addplot(sup_line, color=_SUPPORT, linestyle="--", width=1.2, alpha=0.7))
        addplots.append(mpf.make_addplot(res_line, color=_RESISTANCE, linestyle="--", width=1.2, alpha=0.7))
        addplots.append(mpf.make_addplot(mid_line, color=_MIDPOINT, linestyle=":", width=0.7, alpha=0.5))

    filename = f"{rank:02d}_{result.ticker}_{result.verdict.value}_{result.score:.0f}.png"
    filepath = output_dir / filename

    fig, axes = mpf.plot(
        ohlc,
        type="candle",
        style=_JAPANDI_STYLE,
        volume=True,
        addplot=addplots if addplots else None,
        figsize=(14, 7.5),
        returnfig=True,
        tight_layout=False,
        panel_ratios=(4, 1),
        scale_padding={"left": 0.05, "right": 0.05, "top": 0.3, "bottom": 0.15},
    )

    ax_main = axes[0]
    ax_vol = axes[2]

    # Support/resistance zone shading
    if support and resistance:
        atr_band = (resistance - support) * 0.05
        ax_main.axhspan(support - atr_band, support + atr_band, color=_SUPPORT, alpha=_ZONE_ALPHA)
        ax_main.axhspan(resistance - atr_band, resistance + atr_band, color=_RESISTANCE, alpha=_ZONE_ALPHA)

    # Title block — clean Japandi typography
    title_main = f"{result.ticker}"
    verdict_str = result.verdict.value.replace("_", " ")
    score_str = f"{result.score:.0f}"

    fig.text(0.04, 0.95, title_main, fontsize=22, fontweight="bold", color=_TEXT,
             ha="left", va="top", transform=fig.transFigure)
    fig.text(0.04, 0.91, f"{verdict_str}  ·  Score {score_str}", fontsize=11,
             color=_TEXT_MUTED, ha="left", va="top", transform=fig.transFigure)

    # Metadata line
    meta_parts = []
    if support and resistance:
        meta_parts.append(f"{support:.1f} – {resistance:.1f}")
        if result.range_width_pct:
            meta_parts.append(f"{result.range_width_pct:.1f}% wide")
    if result.rotation_count is not None:
        meta_parts.append(f"{result.rotation_count} rotations")
    if result.structure_score is not None:
        meta_parts.append(f"Str {result.structure_score:.0f} · Reg {result.regime_score:.0f} · Liq {result.liquidity_score:.0f}")

    fig.text(0.04, 0.875, "  |  ".join(meta_parts), fontsize=9,
             color=_TEXT_MUTED, ha="left", va="top", transform=fig.transFigure)

    # Reason at bottom
    if result.reason:
        fig.text(0.5, 0.02, result.reason[:140], fontsize=8, color=_TEXT_MUTED,
                 ha="center", va="bottom", transform=fig.transFigure)

    # Clean up axes
    ax_main.set_ylabel("")
    ax_vol.set_ylabel("")
    for spine in ax_main.spines.values():
        spine.set_visible(False)
    for spine in ax_vol.spines.values():
        spine.set_visible(False)

    fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor=_BG)
    plt.close(fig)

    return filepath
