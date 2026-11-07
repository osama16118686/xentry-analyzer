"""Load OHLCV candles from Binance public API or from a CSV file."""
import sys

import pandas as pd

BINANCE_HOSTS = [
    "https://data-api.binance.vision",
    "https://api.binance.com",
]
COLUMNS = ["time", "open", "high", "low", "close", "volume"]


def _fetch_page(symbol, interval, limit, end_time=None):
    import requests

    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    if end_time is not None:
        params["endTime"] = end_time
    last_error = None
    for host in BINANCE_HOSTS:
        try:
            r = requests.get(f"{host}/api/v3/klines", params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # try the next host
            last_error = e
    raise RuntimeError(f"تعذر جلب البيانات من Binance: {last_error}")


def fetch_klines(symbol="ETHUSDT", interval="4h", limit=1000):
    """Fetch the last `limit` candles from Binance (no API key needed), paging
    backwards 1000 at a time. Returns a DataFrame."""
    rows, end_time = [], None
    while len(rows) < limit:
        page = _fetch_page(symbol, interval, min(1000, limit - len(rows)), end_time)
        if not page:
            break
        rows = page + rows
        end_time = page[0][0] - 1
        if len(page) < 1000:
            break
    df = pd.DataFrame([row[:6] for row in rows], columns=COLUMNS)
    df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
    df[COLUMNS[1:]] = df[COLUMNS[1:]].astype(float)
    return df.set_index("time")


def load_csv(path):
    """Load a CSV with columns time/date, open, high, low, close, volume (case-insensitive)."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "date" in df.columns and "time" not in df.columns:
        df = df.rename(columns={"date": "time"})
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"أعمدة ناقصة في الملف: {missing}")
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df[COLUMNS[1:]] = df[COLUMNS[1:]].astype(float)
    return df[COLUMNS].set_index("time").sort_index()


def get_data(symbol=None, interval="4h", csv=None, limit=1000):
    if csv:
        return load_csv(csv)
    try:
        return fetch_klines(symbol, interval, limit)
    except RuntimeError as e:
        sys.exit(f"{e}\nاستخدم --csv لتحميل البيانات من ملف بدلاً من ذلك.")
