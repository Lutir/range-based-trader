import csv
from pathlib import Path

from rich.console import Console
from rich.table import Table

from range_scanner.models import TickerScanResult

console = Console()

CSV_COLUMNS = [
    "ticker", "score", "verdict", "setup_type", "context_score",
    "entry_quality", "edge_position", "breakout_risk",
    "structure_score", "regime_score", "liquidity_score",
    "support", "resistance", "range_width_pct", "position_in_range",
    "support_touches", "resistance_touches", "containment_ratio",
    "rotation_count", "tightness", "trend_leakage",
    "gap_frequency", "avg_gap_pct", "compression_ratio", "compression_label",
    "adx_14", "atr_pct", "ema20_slope_pct", "avg_volume_20", "avg_dollar_volume_20",
    "latest_close", "data_start", "data_end", "risk_note", "reason", "skip_reason",
]


def write_csv(results: list[TickerScanResult], path: Path) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in results:
            row = {
                "ticker": r.ticker,
                "score": r.score,
                "verdict": r.verdict.value,
                "setup_type": r.setup_type.value if r.setup_type else "",
                "context_score": r.context_score if r.context_score is not None else "",
                "entry_quality": r.entry_quality if r.entry_quality is not None else "",
                "edge_position": r.edge_position.value if r.edge_position else "",
                "breakout_risk": r.breakout_risk.value if r.breakout_risk else "",
                "structure_score": r.structure_score if r.structure_score is not None else "",
                "regime_score": r.regime_score if r.regime_score is not None else "",
                "liquidity_score": r.liquidity_score if r.liquidity_score is not None else "",
                "support": r.support if r.support is not None else "",
                "resistance": r.resistance if r.resistance is not None else "",
                "range_width_pct": r.range_width_pct if r.range_width_pct is not None else "",
                "position_in_range": r.position_in_range if r.position_in_range is not None else "",
                "support_touches": r.support_touches if r.support_touches is not None else "",
                "resistance_touches": r.resistance_touches if r.resistance_touches is not None else "",
                "containment_ratio": r.containment_ratio if r.containment_ratio is not None else "",
                "rotation_count": r.rotation_count if r.rotation_count is not None else "",
                "tightness": r.tightness if r.tightness is not None else "",
                "trend_leakage": r.trend_leakage if r.trend_leakage is not None else "",
                "gap_frequency": r.gap_frequency if r.gap_frequency is not None else "",
                "avg_gap_pct": r.avg_gap_pct if r.avg_gap_pct is not None else "",
                "compression_ratio": r.compression_ratio if r.compression_ratio is not None else "",
                "compression_label": r.compression_label or "",
                "adx_14": r.adx_14 if r.adx_14 is not None else "",
                "atr_pct": r.atr_pct if r.atr_pct is not None else "",
                "ema20_slope_pct": r.ema20_slope_pct if r.ema20_slope_pct is not None else "",
                "avg_volume_20": r.avg_volume_20 if r.avg_volume_20 is not None else "",
                "avg_dollar_volume_20": r.avg_dollar_volume_20 if r.avg_dollar_volume_20 is not None else "",
                "latest_close": r.latest_close if r.latest_close is not None else "",
                "data_start": r.data_start or "",
                "data_end": r.data_end or "",
                "risk_note": r.risk_note,
                "reason": r.reason,
                "skip_reason": r.skip_reason,
            }
            writer.writerow(row)


def print_summary(results: list[TickerScanResult], top: int, total_scanned: int) -> None:
    passed = [r for r in results if r.skip_reason == ""]
    skipped = [r for r in results if r.skip_reason != ""]

    console.print(f"\n[bold]Scanned:[/bold] {total_scanned}")
    console.print(f"[bold]Passed filters:[/bold] {len(passed)}")
    console.print(f"[bold]Skipped:[/bold] {len(skipped)}")
    console.print()

    ranked = sorted(passed, key=lambda r: r.score, reverse=True)[:top]
    if not ranked:
        console.print("[yellow]No range candidates found.[/yellow]")
        return

    table = Table(title="Top Range Candidates", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Ticker", style="bold", width=6)
    table.add_column("Rng", width=4)
    table.add_column("Ent", width=4)
    table.add_column("Ctx", width=4)
    table.add_column("Setup", width=22)
    table.add_column("Edge", width=16)
    table.add_column("Range", width=14)
    table.add_column("Reason")

    for i, r in enumerate(ranked, 1):
        range_str = f"{r.support:.1f}–{r.resistance:.1f}" if r.support and r.resistance else "N/A"
        entry_str = f"{r.entry_quality:.0f}" if r.entry_quality is not None else "–"
        ctx_str = f"{r.context_score:.0f}" if r.context_score is not None else "–"
        edge_str = r.edge_position.value.replace("_", " ") if r.edge_position else "–"
        setup_str = r.setup_type.value.replace("_", " ") if r.setup_type else "–"
        table.add_row(
            str(i), r.ticker, f"{r.score:.0f}", entry_str, ctx_str,
            setup_str, edge_str, range_str, r.reason,
        )

    console.print(table)
