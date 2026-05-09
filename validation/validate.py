"""
Validation tool: compare scanner verdicts against human labels.

HOW TO USE:
1. Run the scanner on a universe:
   python -m range_scanner --universe nasdaq100 --context --output results/nasdaq100.csv

2. Review the top 50-100 results visually (use --charts)

3. For each ticker, add a row to validation/labels.csv:
   ticker,scanner_verdict,human_label,notes
   ADSK,RANGE_PRESSING_RESISTANCE,VALID_RANGE,clean rotational structure
   NVDA,BROKEN_UP,CORRECT_REJECT,clearly broke out
   MU,TOO_WIDE,CORRECT_REJECT,not a real range

4. Run this script to see agreement rate:
   python validation/validate.py

HUMAN LABELS to use:
  CLEAN_RANGE          - Yes, this is a legitimate tradable range
  VALID_BUT_WIDE       - Range exists but too wide for tight trades
  CORRECT_REJECT       - Scanner was right to reject/penalize this
  FALSE_POSITIVE       - Scanner scored it high but it's NOT a good range
  FALSE_NEGATIVE       - Scanner scored it low but it IS a good range
  BREAKOUT_CANDIDATE   - Range is valid but likely to break soon
  MESSY_BUT_TRADEABLE  - Not clean, but experienced traders could work it
"""

import csv
import sys
from pathlib import Path
from collections import Counter


def load_labels(path: Path) -> list[dict]:
    """Load human-labeled validation data."""
    with open(path) as f:
        return list(csv.DictReader(f))


def load_results(path: Path) -> dict[str, dict]:
    """Load scanner results indexed by ticker."""
    with open(path) as f:
        return {row["ticker"]: row for row in csv.DictReader(f)}


def compute_agreement(labels: list[dict], results: dict[str, dict]) -> None:
    """Compare scanner verdicts vs human labels and print report."""
    if not labels:
        print("No labels found. Add rows to validation/labels.csv first.")
        print("See docstring at top of this file for instructions.")
        return

    total = len(labels)
    matches = 0
    false_positives = 0
    false_negatives = 0
    correct_rejects = 0

    verdict_counts: Counter = Counter()
    label_counts: Counter = Counter()

    print(f"\n{'='*70}")
    print(f"  VALIDATION REPORT — {total} labeled tickers")
    print(f"{'='*70}\n")

    mismatches = []

    for row in labels:
        ticker = row["ticker"]
        human = row["human_label"]
        label_counts[human] += 1

        scanner_row = results.get(ticker)
        if not scanner_row:
            print(f"  [SKIP] {ticker} — not found in scanner results")
            continue

        scanner_verdict = scanner_row["verdict"]
        verdict_counts[scanner_verdict] += 1

        # Agreement logic
        if human == "CORRECT_REJECT":
            if scanner_verdict in ("TRENDING_NOT_RANGE", "TOO_WIDE", "BROKEN_UP",
                                   "BROKEN_DOWN", "WIDE_RANGE", "ILLIQUID"):
                matches += 1
                correct_rejects += 1
            else:
                mismatches.append((ticker, scanner_verdict, human, "Scanner didn't reject"))

        elif human in ("CLEAN_RANGE", "MESSY_BUT_TRADEABLE"):
            if scanner_verdict in ("EXCELLENT_RANGE", "RANGE_PRESSING_RESISTANCE",
                                   "RANGE_PRESSING_SUPPORT", "WATCHLIST"):
                matches += 1
            else:
                false_negatives += 1
                mismatches.append((ticker, scanner_verdict, human, "Scanner missed a valid range"))

        elif human == "FALSE_POSITIVE":
            false_positives += 1
            mismatches.append((ticker, scanner_verdict, human, "Scanner scored too high"))

        elif human == "FALSE_NEGATIVE":
            false_negatives += 1
            mismatches.append((ticker, scanner_verdict, human, "Scanner scored too low"))

        elif human == "VALID_BUT_WIDE":
            if scanner_verdict in ("WIDE_RANGE", "WATCHLIST"):
                matches += 1
            else:
                mismatches.append((ticker, scanner_verdict, human, "Width classification off"))

        elif human == "BREAKOUT_CANDIDATE":
            if "PRESSING" in scanner_verdict or "BROKEN" in scanner_verdict:
                matches += 1
            else:
                mismatches.append((ticker, scanner_verdict, human, "Didn't flag breakout"))
        else:
            matches += 1

    agreement_rate = matches / total * 100 if total > 0 else 0

    print(f"  Agreement rate: {agreement_rate:.1f}% ({matches}/{total})")
    print(f"  False positives: {false_positives}")
    print(f"  False negatives: {false_negatives}")
    print(f"  Correct rejects: {correct_rejects}")
    print()

    if mismatches:
        print(f"  {'─'*70}")
        print(f"  MISMATCHES:")
        print(f"  {'─'*70}")
        for ticker, verdict, human, note in mismatches:
            print(f"  {ticker:8} scanner={verdict:24} human={human:20} ({note})")
        print()

    print(f"  {'─'*70}")
    print(f"  LABEL DISTRIBUTION:")
    for label, count in label_counts.most_common():
        print(f"    {label:24} {count}")
    print()


if __name__ == "__main__":
    labels_path = Path("validation/labels.csv")
    results_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results/nasdaq100.csv")

    if not labels_path.exists():
        print(f"Labels file not found: {labels_path}")
        sys.exit(1)
    if not results_path.exists():
        print(f"Results file not found: {results_path}")
        print(f"Usage: python validation/validate.py [results_csv_path]")
        sys.exit(1)

    labels = load_labels(labels_path)
    results = load_results(results_path)
    compute_agreement(labels, results)
