import csv
from pathlib import Path

from rich.console import Console
from rich.table import Table

from range_scanner.models import TickerScanResult

console = Console()

CSV_COLUMNS = [
    "ticker", "score", "verdict", "support", "resistance", "range_width_pct",
    "support_touches", "resistance_touches", "containment_ratio", "adx_14",
    "atr_pct", "ema20_slope_pct", "avg_volume_20", "avg_dollar_volume_20",
    "latest_close", "risk_note", "skip_reason",
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
                "support": r.support if r.support is not None else "",
                "resistance": r.resistance if r.resistance is not None else "",
                "range_width_pct": r.range_width_pct if r.range_width_pct is not None else "",
                "support_touches": r.support_touches if r.support_touches is not None else "",
                "resistance_touches": r.resistance_touches if r.resistance_touches is not None else "",
                "containment_ratio": r.containment_ratio if r.containment_ratio is not None else "",
                "adx_14": r.adx_14 if r.adx_14 is not None else "",
                "atr_pct": r.atr_pct if r.atr_pct is not None else "",
                "ema20_slope_pct": r.ema20_slope_pct if r.ema20_slope_pct is not None else "",
                "avg_volume_20": r.avg_volume_20 if r.avg_volume_20 is not None else "",
                "avg_dollar_volume_20": r.avg_dollar_volume_20 if r.avg_dollar_volume_20 is not None else "",
                "latest_close": r.latest_close if r.latest_close is not None else "",
                "risk_note": r.risk_note,
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

    table = Table(title="Top Range Candidates")
    table.add_column("#", style="dim")
    table.add_column("Ticker", style="bold")
    table.add_column("Score")
    table.add_column("Verdict")
    table.add_column("Range")

    for i, r in enumerate(ranked, 1):
        range_str = f"{r.support:.2f}–{r.resistance:.2f}" if r.support and r.resistance else "N/A"
        table.add_row(str(i), r.ticker, f"{r.score:.1f}", r.verdict.value, range_str)

    console.print(table)
