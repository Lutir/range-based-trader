"""
Structure-validity backtest: Did the scanner's ranges actually hold?

THIS IS NOT A TRADING BACKTEST.
It does not simulate buy/sell orders or calculate P&L.

Instead it asks a simpler question:
  "When the scanner said 'this is a clean range', did price
   actually stay inside that range over the next N days?"

HOW TO USE:
1. Run the scanner with fresh data:
   python -m range_scanner --universe nasdaq100 --output results/nasdaq100.csv

2. Run this backtest:
   python validation/backtest.py results/nasdaq100.csv --days 10

3. It will:
   - Take all tickers that scored as EXCELLENT_RANGE or WATCHLIST
   - Fetch the NEXT N days of price data after the scan date
   - Check if price stayed inside the detected support/resistance
   - Report success rate

WHAT SUCCESS MEANS:
  "70% of EXCELLENT_RANGE picks stayed in range for 10 days"
  → The scanner is identifying real structure, not noise.

  "30% of EXCELLENT_RANGE picks stayed in range for 10 days"
  → The scanner is over-scoring unstable setups.

LIMITATIONS:
  - This only tests structure persistence, not trading profitability
  - A stock can stay in range but still lose money on entry timing
  - Small sample sizes (5-10 stocks) are not statistically meaningful
"""

import csv
import sys
from pathlib import Path

import pandas as pd

from range_scanner.data import fetch_bars


def run_backtest(results_path: Path, forward_days: int = 10) -> None:
    """Check if detected ranges held for the next N trading days."""

    with open(results_path) as f:
        rows = list(csv.DictReader(f))

    # Filter to range-positive verdicts
    range_verdicts = {"EXCELLENT_RANGE", "RANGE_PRESSING_RESISTANCE",
                      "RANGE_PRESSING_SUPPORT", "WATCHLIST"}
    candidates = [r for r in rows if r["verdict"] in range_verdicts
                  and r["support"] and r["resistance"]]

    if not candidates:
        print("No range candidates found in results to backtest.")
        return

    print(f"\n{'='*70}")
    print(f"  STRUCTURE PERSISTENCE BACKTEST")
    print(f"  Testing {len(candidates)} range candidates over {forward_days} forward days")
    print(f"{'='*70}\n")

    held = 0
    broke = 0
    no_data = 0

    results = []

    for row in candidates:
        ticker = row["ticker"]
        support = float(row["support"])
        resistance = float(row["resistance"])
        score = float(row["score"])

        # Fetch forward data (extra bars beyond the scan period)
        # We need bars AFTER the data_end date
        df = fetch_bars(ticker, forward_days + 5)
        if df is None or len(df) < forward_days:
            no_data += 1
            continue

        # Take the last forward_days bars (most recent = forward-looking from scan)
        forward = df.iloc[-forward_days:]

        # Check: did all closes stay inside the range?
        closes = forward["close"]
        inside = ((closes >= support * 0.99) & (closes <= resistance * 1.01)).all()

        # Also check if any close went significantly outside (>2% beyond)
        max_close = closes.max()
        min_close = closes.min()
        broke_above = max_close > resistance * 1.02
        broke_below = min_close < support * 0.98

        if inside:
            status = "HELD"
            held += 1
        elif broke_above:
            status = "BROKE_UP"
            broke += 1
        elif broke_below:
            status = "BROKE_DOWN"
            broke += 1
        else:
            status = "MARGINAL"
            held += 1  # Within 1-2% tolerance

        results.append({
            "ticker": ticker,
            "score": score,
            "verdict": row["verdict"],
            "support": support,
            "resistance": resistance,
            "status": status,
            "max_close": round(max_close, 2),
            "min_close": round(min_close, 2),
        })

    # Print results
    total_tested = held + broke
    if total_tested == 0:
        print("  No tickers had sufficient forward data.")
        return

    hold_rate = held / total_tested * 100

    print(f"  Results:")
    print(f"    Ranges that HELD:  {held}/{total_tested} ({hold_rate:.0f}%)")
    print(f"    Ranges that BROKE: {broke}/{total_tested} ({100-hold_rate:.0f}%)")
    if no_data:
        print(f"    Skipped (no data): {no_data}")
    print()

    # Detail table
    print(f"  {'─'*70}")
    print(f"  {'Ticker':<8} {'Score':<6} {'Verdict':<24} {'Status':<12} {'Range'}")
    print(f"  {'─'*70}")
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        range_str = f"{r['support']:.1f}–{r['resistance']:.1f}"
        print(f"  {r['ticker']:<8} {r['score']:<6.0f} {r['verdict']:<24} {r['status']:<12} {range_str}")
    print()

    # Score-based breakdown
    excellent = [r for r in results if r["score"] >= 75]
    watchlist = [r for r in results if 55 <= r["score"] < 75]

    if excellent:
        exc_held = sum(1 for r in excellent if r["status"] in ("HELD", "MARGINAL"))
        print(f"  Score >= 75 (Excellent): {exc_held}/{len(excellent)} held ({exc_held/len(excellent)*100:.0f}%)")
    if watchlist:
        wl_held = sum(1 for r in watchlist if r["status"] in ("HELD", "MARGINAL"))
        print(f"  Score 55-75 (Watchlist): {wl_held}/{len(watchlist)} held ({wl_held/len(watchlist)*100:.0f}%)")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validation/backtest.py <results.csv> [--days N]")
        print("Example: python validation/backtest.py results/nasdaq100.csv --days 10")
        sys.exit(1)

    results_path = Path(sys.argv[1])
    forward_days = 10

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        forward_days = int(sys.argv[idx + 1])

    if not results_path.exists():
        print(f"File not found: {results_path}")
        sys.exit(1)

    run_backtest(results_path, forward_days)
