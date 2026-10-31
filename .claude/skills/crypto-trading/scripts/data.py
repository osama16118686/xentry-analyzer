"""Load OHLCV candles from Binance public API or from a CSV file."""
import sys

import pandas as pd

BINANCE_HOSTS = [
    "https://data-api.binance.vision",
    "https://api.binance.com",
]
COLUMNS = ["time", "open", "high", "low", "close", "volume"]


def fetch_klines(symbol="ETHUSDT", interval="4h", limit=1000):
    """Fetch candles from Binance (no API key needed). Returns a DataFrame."""
    import requests

    last_error = None
    for host in BINANCE_HOSTS:
        try:
            r = requests.get(
                f"{host}/api/v3/klines",
                params={"symbol": symbol.upper(), "interval": interval, "limit": limit},
                timeout=15,
            )
            r.raise_for_status()
            rows = r.json()
            df = pd.DataFrame([row[:6] for row in rows], columns=COLUMNS)
            df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
            df[COLUMNS[1:]] = df[COLUMNS[1:]].astype(float)
            return df.set_index("time")
        except Exception as e:  # try the next host
            last_error = e
    raise RuntimeError(f"تعذر جلب البيانات من Binance: {last_error}")


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
