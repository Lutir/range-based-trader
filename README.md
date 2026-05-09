# Range Candidate Scanner

A professional-grade CLI tool that scans stock tickers for range-bound structure, classifies the current state of each range, assesses market context, and outputs actionable setup types.

This is a **market-structure filter and setup classifier** — not a trading bot or prediction system.

```
                                    RANGE SCANNER
    ┌─────────────────────────────────────────────────────────────────────┐
    │                                                                     │
    │   Tickers ──► Structure Detection ──► State Classification          │
    │                                              │                      │
    │                                              ▼                      │
    │              Market Context ──────► Setup Classification             │
    │              (SPY/QQQ/Sector)                 │                      │
    │                                              ▼                      │
    │                                    Ranked Results + Charts           │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## What It Answers

The scanner provides four layers of analysis per ticker:

```
    ┌──────────────────────────────────────────────────────────────┐
    │  Layer 1: RANGE QUALITY                                      │
    │  "Is this chart structurally range-bound?"                   │
    │  ─────────────────────────────────────────                   │
    │  Rotation count, reaction strength, containment,             │
    │  tightness, range width, trend leakage                       │
    ├──────────────────────────────────────────────────────────────┤
    │  Layer 2: ENTRY QUALITY                                      │
    │  "Is price at a useful edge right now?"                      │
    │  ─────────────────────────────────────────                   │
    │  Position in range, edge proximity, breakout risk            │
    ├──────────────────────────────────────────────────────────────┤
    │  Layer 3: CONTEXT QUALITY                                    │
    │  "Does the market/sector environment support this?"          │
    │  ─────────────────────────────────────────                   │
    │  Market regime, sector trend, relative strength vs SPY       │
    ├──────────────────────────────────────────────────────────────┤
    │  Layer 4: SETUP TYPE                                         │
    │  "What kind of setup is this, if any?"                       │
    │  ─────────────────────────────────────────                   │
    │  Mean reversion long/short, breakout watch,                  │
    │  monitor only, avoid context conflict                        │
    └──────────────────────────────────────────────────────────────┘
```

---

## Install

```bash
pip install -e ".[dev]"
```

## Setup

Create a `.env` file:

```env
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://data.alpaca.markets
```

Free [Alpaca](https://alpaca.markets/) paper trading account works.

---

## Usage

### Basic scan

```bash
python -m range_scanner --tickers tickers.txt --output results.csv
```

### Universe scan with context

```bash
python -m range_scanner --universe nasdaq100 --context --output results/nasdaq100.csv --top 20
```

### With chart export

```bash
python -m range_scanner --universe nasdaq100 --context --charts --top 10
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--tickers` | `tickers.txt` | Path to ticker file |
| `--universe` | — | Built-in universe: `personal`, `nasdaq100`, `etfs` |
| `--lookback` | `120` | Number of daily candles |
| `--output` | `results.csv` | CSV output path |
| `--min-volume` | `1000000` | Min average daily volume |
| `--min-dollar-volume` | `20000000` | Min average dollar volume |
| `--top` | `20` | Results to display |
| `--charts` | off | Export PNG charts for top candidates |
| `--charts-dir` | `charts/` | Chart output directory |
| `--context` | off | Add market/sector context layer |

---

## Built-in Universes

```
universes/
  personal.txt      Your watchlist
  nasdaq100.txt     Nasdaq-100 components
  etfs.txt          Major ETFs (sector, bond, commodity)
```

---

## Output Example

```
Market regime: RISK ON TRENDING
  SPY ADX=22.2 slope=6.95% | QQQ ADX=36.9 slope=11.23%

┌───┬────────┬─────┬─────┬─────┬───────────────────────┬────────────────┬─────────────┐
│ # │ Ticker │ Rng │ Ent │ Ctx │ Setup                 │ Edge           │ Range       │
├───┼────────┼─────┼─────┼─────┼───────────────────────┼────────────────┼─────────────┤
│ 1 │ ADSK   │  81 │  66 │  75 │ BREAKOUT WATCH UPSIDE │ NEAR RESIST.   │ 229–247     │
│ 2 │ GME    │  78 │  41 │  55 │ RANGE MONITOR ONLY    │ UPPER HALF     │ 22.5–25.0   │
│ 3 │ TMO    │  65 │  76 │  25 │ AVOID CONTEXT CONFL.  │ NEAR SUPPORT   │ 457–525     │
│ 4 │ NVDA   │  40 │   0 │   0 │ NOT RANGE TRADE       │ BROKEN UP      │ 177–194     │
└───┴────────┴─────┴─────┴─────┴───────────────────────┴────────────────┴─────────────┘
```

### Reading the scores

```
    Rng = Range Quality (0-100)     "Is the structure good?"
    Ent = Entry Quality (0-100)     "Is the timing good?"
    Ctx = Context Score (0-100)     "Is the environment supportive?"
```

---

## Verdicts

```
    EXCELLENT_RANGE             Clean structure, active, tradable
    RANGE_PRESSING_RESISTANCE   Valid range, price near upper zone
    RANGE_PRESSING_SUPPORT      Valid range, price near lower zone
    WATCHLIST                   Decent range, not at an edge
    WIDE_RANGE                  15-25% width — watchlist only
    MESSY_RANGE                 Weak structure
    BROKEN_UP                   Price exited above resistance
    BROKEN_DOWN                 Price exited below support
    TOO_WIDE                    >25% width — rejected
    TRENDING_NOT_RANGE          ADX/slope/leakage too high
    ILLIQUID                    Below volume thresholds
```

---

## Setup Types

When `--context` is enabled, each ticker gets a setup classification:

```
    ┌─────────────────────────────────────────────────────────────────┐
    │                                                                 │
    │  MEAN_REVERSION_LONG                                            │
    │  Near support + favorable context + acceptable RS               │
    │                                                                 │
    │  MEAN_REVERSION_SHORT                                           │
    │  Near resistance + calm market + low breakout risk              │
    │                                                                 │
    │  BREAKOUT_WATCH_UPSIDE                                          │
    │  Near resistance + risk-on market + sector trending up          │
    │                                                                 │
    │  BREAKDOWN_WATCH_DOWNSIDE                                       │
    │  Near support + high breakdown risk + volume elevated           │
    │                                                                 │
    │  RANGE_MONITOR_ONLY                                             │
    │  Valid range but mid-range or no clear directional edge         │
    │                                                                 │
    │  AVOID_CONTEXT_CONFLICT                                         │
    │  Edge exists but context fights the setup                       │
    │  (e.g. near support but badly underperforming in risk-on)       │
    │                                                                 │
    │  NOT_RANGE_TRADE                                                │
    │  Broken, trending, or structurally invalid                      │
    │                                                                 │
    └─────────────────────────────────────────────────────────────────┘
```

---

## How It Works

```
    ┌───────────────────────────────────────────────────────────────────┐
    │                         DATA LAYER                                │
    │  Alpaca API ──► Daily OHLCV ──► Paginated fetch ──► Last N bars  │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │
    ┌─────────────────────────────────▼─────────────────────────────────┐
    │                      STRUCTURE DETECTION                          │
    │                                                                   │
    │  Pivot highs/lows (window=3)                                      │
    │       │                                                           │
    │       ▼                                                           │
    │  Cluster into zones (ATR-adjusted tolerance)                      │
    │       │                                                           │
    │       ▼                                                           │
    │  Select support/resistance (recency-weighted)                     │
    │       │                                                           │
    │       ▼                                                           │
    │  Measure: touches, reactions, rotations, containment, tightness   │
    │       │                                                           │
    │       ▼                                                           │
    │  Detect: trend leakage (HH/HL patterns)                          │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │
    ┌─────────────────────────────────▼─────────────────────────────────┐
    │                         SCORING                                   │
    │                                                                   │
    │  Rotation (20%) + Reaction (10%) + Containment (10%)              │
    │  + Tightness (8%) + Width (7%) + Touches (10%)                    │
    │  + ADX (10%) + EMA slope (5%) + Trend leakage (10%)               │
    │  + Liquidity (5%) + ATR stability (5%)                            │
    │                                                                   │
    │  Hard caps: >25% width = max 30, >15% = max 50, <2 rot = max 55  │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │
    ┌─────────────────────────────────▼─────────────────────────────────┐
    │                    STATE CLASSIFICATION                           │
    │                                                                   │
    │  Position in range ──► Edge position ──► Breakout risk            │
    │                                                                   │
    │  Recent validity: BROKEN_UP / BROKEN_DOWN / STALE / ACTIVE        │
    └─────────────────────────────────┬─────────────────────────────────┘
                                      │
    ┌─────────────────────────────────▼─────────────────────────────────┐
    │                    CONTEXT LAYER (--context)                      │
    │                                                                   │
    │  Market regime (SPY/QQQ ADX + slope)                              │
    │  Sector regime (sector ETF trend)                                 │
    │  Relative strength vs SPY (20-day)                                │
    │       │                                                           │
    │       ▼                                                           │
    │  Setup type classification                                        │
    │  Context score                                                    │
    └───────────────────────────────────────────────────────────────────┘
```

---

## Scoring Deep Dive

### Range Quality Score (0-100)

```
    Component               Weight    What scores high
    ─────────────────────   ──────    ─────────────────────────────
    Rotation count          20%       8+ full rotations between zones
    Reaction strength       10%       Strong reversals after touches
    Containment ratio       10%       85%+ closes inside range
    Tightness               8%        Full range utilization (not midpoint clustering)
    Range width             7%        3-8% ideal sweet spot
    Support touches         5%        4+ confirmed reactions
    Resistance touches      5%        4+ confirmed reactions
    ADX                     10%       Below 20 (no trend)
    EMA slope               5%        Below 2% (flat)
    Trend leakage           10%       No HH/HL or LH/LL pattern
    Liquidity               5%        Dollar volume well above threshold
    ATR stability           5%        1-6% daily range
```

### Entry Quality Score (0-100)

```
    Near edge (support or resistance)     = high
    Mid-range                             = low
    High breakout risk at the edge        = penalized
    Broken out of range                   = zero
```

### Context Score (0-100)

```
    Calm market + stable sector + good RS      = 80-100
    Risk-on + sector trending with setup       = 65-80
    Mixed signals                              = 40-60
    Context fights the setup                   = 0-25
```

---

## Chart Export

Charts use a Japandi-inspired palette — warm linen backgrounds, sage green up-candles, terracotta down-candles.

Each chart includes:
- Candlestick price action
- Support zone (green dashed + shaded band)
- Resistance zone (terracotta dashed + shaded band)
- Midpoint reference line
- Title: ticker, verdict, score
- Metadata: range, width, rotations, sub-scores
- Reason string at bottom

---

## Project Structure

```
range-scanner/
  CLAUDE.md                   Project spec
  README.md                   This file
  pyproject.toml              Dependencies and build config
  .env                        API keys (git-ignored)
  tickers.txt                 Default ticker list

  universes/
    personal.txt              Personal watchlist
    nasdaq100.txt             Nasdaq-100 components
    etfs.txt                  ETF universe

  src/range_scanner/
    __init__.py
    __main__.py               Entry point
    cli.py                    Typer CLI with scan command
    config.py                 All thresholds in one config object
    data.py                   Alpaca API client (paginated, retry)
    indicators.py             ATR, ADX, EMA calculations
    structure.py              Pivot detection, zones, rotations, tightness
    scoring.py                Weighted scoring + verdict classification
    state.py                  Edge position, entry quality, breakout risk
    context.py                Market regime, sector, relative strength
    setup.py                  Setup type classification
    output.py                 CSV writer + rich console table
    charts.py                 Japandi-styled PNG chart export
    models.py                 Pydantic models for all data structures

  tests/
    test_indicators.py        ATR, ADX, EMA tests
    test_structure.py         Pivot, clustering, rotation, tightness tests
    test_scoring.py           Scoring functions + verdict + sub-scores

  results/                    Scan outputs by universe
  charts/                     Exported chart PNGs
```

---

## Tests

```bash
pytest tests/ -v
```

69 unit tests covering indicators, structure detection, scoring, verdicts, and sub-scores.

---

## Limitations

- Support/resistance detection is approximate (pivot clustering, not volume profile)
- A high score does not mean a good trade
- A clean range can break immediately after detection
- Earnings dates not yet integrated (placeholder for Sprint 7)
- Context layer requires extra API calls (~3-5 additional tickers)
- The system answers "what kind of setup is this?" not "should I trade this?"

---

## Philosophy

```
    ┌─────────────────────────────────────────────────────────────┐
    │                                                             │
    │   The scanner does NOT predict price.                       │
    │                                                             │
    │   It classifies structure, assesses context,                │
    │   and tells you what kind of situation you're looking at.   │
    │                                                             │
    │   The human decides whether to act.                         │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘
```
