import os
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0


def _get_headers() -> dict[str, str]:
    return {
        "APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
        "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"],
    }


def _get_base_url() -> str:
    return os.environ.get("ALPACA_BASE_URL", "https://data.alpaca.markets")


def fetch_bars(ticker: str, lookback: int) -> pd.DataFrame | None:
    base_url = _get_base_url()
    url = f"{base_url}/v2/stocks/{ticker}/bars"
    start_date = (datetime.now() - timedelta(days=int(lookback * 1.7))).strftime("%Y-%m-%d")
    headers = _get_headers()

    all_bars: list[dict] = []
    page_token: str | None = None

    while True:
        params: dict = {
            "timeframe": "1Day",
            "limit": 1000,
            "start": start_date,
            "adjustment": "split",
            "sort": "asc",
        }
        if page_token:
            params["page_token"] = page_token

        success = False
        for attempt in range(_MAX_RETRIES):
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            if resp.status_code == 200:
                success = True
                break
            if resp.status_code == 429:
                time.sleep(_BACKOFF_BASE * (2 ** attempt))
                continue
            return None

        if not success:
            return None

        data = resp.json()
        bars = data.get("bars")
        if bars:
            all_bars.extend(bars)

        page_token = data.get("next_page_token")
        if not page_token:
            break

    if not all_bars:
        return None

    df = pd.DataFrame(all_bars)
    rename_map = {"t": "timestamp", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"}
    df = df.rename(columns=rename_map)

    required = ["timestamp", "open", "high", "low", "close", "volume"]
    for col in required:
        if col not in df.columns:
            return None

    df = df[required]
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["high"] = pd.to_numeric(df["high"], errors="coerce")
    df["low"] = pd.to_numeric(df["low"], errors="coerce")
    df["open"] = pd.to_numeric(df["open"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")

    # Take the last `lookback` bars to ensure we use the most recent data
    if len(df) > lookback:
        df = df.iloc[-lookback:]

    return df.reset_index(drop=True)
