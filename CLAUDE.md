# Project: Range Candidate Scanner

## Mission

Build a local Python tool that scans a user-provided list of stock tickers and ranks which ones currently show the cleanest range-bound structure.

This is NOT a trading bot.
This is NOT a price prediction system.
This is NOT financial advice.

The system is a market-structure filter.

Primary question:

> "From this list of stocks, which charts are most worth manually reviewing for range-based trading?"

---

## Hard Scope

Build a CLI-first MVP.

Input:
- A text file of tickers.

Output:
- A ranked CSV file.
- A console summary of top candidates.

No dashboard in MVP.
No live trading.
No websocket.
No machine learning.
No automated buy/sell recommendations.

---

## MVP Goal

Given 50–500 tickers, fetch recent daily OHLCV data and produce:

```text
ticker, score, verdict, support, resistance, range_width_pct, adx, atr_pct, containment_ratio, avg_dollar_volume
```

Example:

```
AAPL, 74, WATCHLIST, 284.10, 294.20, 3.56, 18.4, 1.42, 0.81, 4800000000
```

## Tech Stack

Language: Python 3.11+

Data provider: Alpaca Market Data API

Core libraries:
- pandas
- numpy
- requests or alpaca-py
- pydantic
- typer
- pytest

Optional: rich for CLI formatting

Do NOT introduce FastAPI, Streamlit, React, ML, or databases in MVP.

## Command Line Interface

```
python -m range_scanner scan --tickers tickers.txt --lookback 120 --output results.csv
```

Options:
- `--tickers` path to ticker file
- `--lookback` number of daily candles, default 120
- `--output` CSV output path, default results.csv
- `--min-volume` minimum average daily volume, default 1_000_000
- `--min-dollar-volume` default 20_000_000
- `--top` number of top results printed to console, default 20

## Engineering Standards

- Typed where practical
- Deterministic
- Testable
- Modular
- All thresholds in config object
- No silent exception swallowing
- Every skipped ticker must include a reason
