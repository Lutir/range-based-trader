# Range Candidate Scanner

A local Python CLI tool that scans a list of stock tickers and ranks which ones currently show the cleanest range-bound structure. It reduces manual chart review time by surfacing candidates worth investigating for range-based trading setups.

This is a **market-structure filter**, not a trading bot or prediction system.

## Install

```bash
pip install -e ".[dev]"
```

## Setup

Create a `.env` file (or export environment variables):

```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://data.alpaca.markets
```

You need an [Alpaca](https://alpaca.markets/) account (free paper trading account works).

## Usage

```bash
python -m range_scanner --tickers tickers.txt --output results.csv
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--tickers` | `tickers.txt` | Path to file with one ticker per line |
| `--lookback` | `120` | Number of daily candles to fetch |
| `--output` | `results.csv` | CSV output path |
| `--min-volume` | `1000000` | Minimum average daily volume |
| `--min-dollar-volume` | `20000000` | Minimum average daily dollar volume |
| `--top` | `20` | Number of top results to print |

### Ticker File Format

One ticker per line, `#` lines ignored:

```
AAPL
MSFT
GOOGL
# skip this one
AMZN
```

## Output

### Console

Prints a ranked table of top candidates with score, verdict, and detected range.

### CSV

Full results with all metrics:

| Column | Description |
|--------|-------------|
| `ticker` | Stock symbol |
| `score` | 0-100 composite range quality score |
| `verdict` | EXCELLENT_RANGE, WATCHLIST, MESSY_RANGE, TRENDING_NOT_RANGE, ILLIQUID, INSUFFICIENT_DATA, ERROR |
| `support` | Detected support zone midpoint |
| `resistance` | Detected resistance zone midpoint |
| `range_width_pct` | Range width as percentage of support |
| `support_touches` | Number of price reactions at support |
| `resistance_touches` | Number of price reactions at resistance |
| `containment_ratio` | Fraction of closes within the range |
| `adx_14` | Average Directional Index (trend strength) |
| `atr_pct` | Average True Range as % of price |
| `ema20_slope_pct` | EMA(20) slope over 20 periods |
| `avg_volume_20` | 20-day average volume |
| `avg_dollar_volume_20` | 20-day average dollar volume |
| `latest_close` | Most recent closing price |
| `risk_note` | Breakout/breakdown risk flag |
| `skip_reason` | Why a ticker was skipped (if applicable) |

## Scoring

The composite score weights these factors:

| Component | Weight |
|-----------|--------|
| Containment ratio | 20% |
| Range width | 15% |
| Support touches | 15% |
| Resistance touches | 15% |
| ADX (low = range-friendly) | 15% |
| Liquidity | 10% |
| EMA slope flatness | 5% |
| ATR stability | 5% |

## How It Works

1. Fetches daily OHLCV data from Alpaca
2. Filters out illiquid or data-insufficient tickers
3. Detects pivot highs/lows and clusters them into support/resistance zones
4. Counts price touches at each zone
5. Measures containment (how well price stays in the range)
6. Computes trend indicators (ADX, EMA slope) to penalize trending stocks
7. Produces a weighted score and verdict

## Tests

```bash
pytest tests/ -v
```

43 unit tests covering indicators, structure detection, and scoring logic.

## Limitations

- Support/resistance detection is approximate (pivot clustering)
- A high score does not mean a good trade
- A clean range can break immediately after detection
- The system answers "is this chart worth reviewing?" not "should I buy this?"
