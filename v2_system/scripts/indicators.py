"""Technical indicators on an OHLCV DataFrame (columns: open, high, low, close, volume)."""
import numpy as np
import pandas as pd


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def sma(s, n):
    return s.rolling(n).mean()


def rsi(close, n=14):
    """Wilder's RSI."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100)


def macd(close, fast=12, slow=26, signal=9):
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return line, sig, line - sig


def bollinger(close, n=20, k=2):
    mid = sma(close, n)
    std = close.rolling(n).std()
    return mid + k * std, mid, mid - k * std


def atr(df, n=14):
    prev_close = df["close"].shift()
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def adx(df, n=14):
    """Wilder's ADX: trend strength, below ~20 means a ranging market."""
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = up.where((up > down) & (up > 0), 0.0)
    minus_dm = down.where((down > up) & (down > 0), 0.0)
    a = atr(df, n)
    plus_di = 100 * plus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    minus_di = 100 * minus_dm.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return dx.fillna(0).ewm(alpha=1 / n, adjust=False).mean()


def add_all(df):
    df = df.copy()
    c = df["close"]
    df["ema20"], df["ema50"], df["ema200"] = ema(c, 20), ema(c, 50), ema(c, 200)
    df["rsi"] = rsi(c)
    df["macd"], df["macd_signal"], df["macd_hist"] = macd(c)
    df["bb_upper"], df["bb_mid"], df["bb_lower"] = bollinger(c)
    df["atr"] = atr(df)
    df["adx"] = adx(df)
    df["vol_ratio"] = df["volume"] / sma(df["volume"], 20)
    df["high20"] = df["high"].rolling(20).max().shift()
    return df


def swing_levels(df, window=5, max_levels=3):
    """Supports below and resistances above the last close, from swing lows/highs,
    merging levels closer than 0.5 ATR."""
    price = df["close"].iloc[-1]
    tol = atr(df).iloc[-1] * 0.5
    highs, lows = df["high"], df["low"]
    w = 2 * window + 1
    piv_hi = highs[highs == highs.rolling(w, center=True).max()].dropna()
    piv_lo = lows[lows == lows.rolling(w, center=True).min()].dropna()

    def cluster(levels):
        out = []
        for lv in sorted(levels):
            if out and abs(lv - out[-1][-1]) <= tol:
                out[-1].append(lv)
            else:
                out.append([lv])
        return [round(float(np.mean(g)), 2) for g in out]

    levels = cluster(list(piv_hi) + list(piv_lo))
    supports = sorted([lv for lv in levels if lv < price], reverse=True)[:max_levels]
    resistances = sorted([lv for lv in levels if lv > price])[:max_levels]
    return supports, resistances
