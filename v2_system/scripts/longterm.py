"""Compare long-term approaches on daily candles: buy & hold, trend following, and DCA.

Usage:
  python longterm.py BTCUSDT ETHUSDT --sma 50 100 200 --dca 100

Each coin gets an equal, separate share of the capital (no rebalancing). Trend
following holds a coin only while its daily close is above its SMA; the decision is
made on a close and applies from that close on, paying fee + slippage on each switch.
All series start on the same day, after the longest SMA has warmed up.
DCA buys `--dca` dollars every 7 days, split equally across the coins.
"""
import argparse
import json

import numpy as np
import pandas as pd

from data import fetch_klines


def stats(equity, days_in_market=None):
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    total = equity.iloc[-1] / equity.iloc[0]
    out = {
        "total_return_pct": round((total - 1) * 100, 1),
        "cagr_pct": round((total ** (1 / years) - 1) * 100, 1) if years > 0 else None,
        "max_drawdown_pct": round((1 - equity / equity.cummax()).max() * 100, 1),
    }
    if days_in_market is not None:
        out["time_in_market_pct"] = round(days_in_market * 100, 1)
    return out


def trend_sleeve(close, n, cost):
    ret = close.pct_change().fillna(0)
    pos = (close > close.rolling(n).mean()).astype(float).shift().fillna(0)  # decided on previous close
    switches = pos.diff().abs().fillna(0)
    return (1 + pos * ret - switches * cost).cumprod(), pos.mean(), int(switches.sum())


def dca(closes, amount, fee):
    """closes: DataFrame of coin closes. Buys every 7 days; returns invested, value, worst ratio."""
    buy_days = closes.index[::7]
    units = pd.Series(0.0, index=closes.columns)
    invested, rows = 0.0, []
    for t, prices in closes.iterrows():
        if t in buy_days:
            units += amount / len(closes.columns) * (1 - fee) / prices
            invested += amount
        rows.append((invested, float((units * prices).sum())))
    inv, val = (np.array(x) for x in zip(*rows))
    ratio = val / inv
    return {
        "invested": round(inv[-1], 0),
        "final_value": round(val[-1], 0),
        "total_return_pct": round((val[-1] / inv[-1] - 1) * 100, 1),
        "worst_value_vs_invested_pct": round((ratio.min() - 1) * 100, 1),
    }


def compare(closes, smas, dca_amount, fee=0.1, slippage=0.05):
    cost = (fee + slippage) / 100
    start = closes.index[max(smas)]
    res = {"period": f"{start:%Y-%m-%d} → {closes.index[-1]:%Y-%m-%d}", "coins": list(closes.columns)}
    view = closes.loc[start:]
    hold = (view / view.iloc[0]).mean(axis=1)
    res["buy_and_hold"] = stats(hold)
    for n in smas:
        sleeves, exposure, trades = [], [], 0
        for c in closes.columns:
            eq, e, k = trend_sleeve(closes[c], n, cost)
            eq = eq.loc[start:]
            sleeves.append(eq / eq.iloc[0])
            exposure.append(closes[c].loc[start:].gt(closes[c].rolling(n).mean().loc[start:]).mean())
            trades += k
        res[f"trend_sma{n}"] = {**stats(pd.concat(sleeves, axis=1).mean(axis=1), float(np.mean(exposure))),
                                "switches": trades}
    res[f"dca_{dca_amount:g}_weekly"] = dca(view, dca_amount, fee / 100)
    return res


def yearly(closes, n, fee=0.1, slippage=0.05):
    cost = (fee + slippage) / 100
    start = closes.index[n]
    hold = (closes.loc[start:] / closes.loc[start:].iloc[0]).mean(axis=1)
    trend = pd.concat([trend_sleeve(closes[c], n, cost)[0].loc[start:] for c in closes.columns], axis=1)
    trend = (trend / trend.iloc[0]).mean(axis=1)
    out = {}
    for y in sorted(set(hold.index.year)):
        h, t = hold[hold.index.year == y], trend[trend.index.year == y]
        out[y] = {"hold_pct": round((h.iloc[-1] / h.iloc[0] - 1) * 100, 1),
                  f"trend_sma{n}_pct": round((t.iloc[-1] / t.iloc[0] - 1) * 100, 1)}
    return out


def load(symbols, limit=4000):
    closes = pd.concat({s: fetch_klines(s, "1d", limit)["close"] for s in symbols}, axis=1).dropna()
    return closes


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("symbols", nargs="*", default=["BTCUSDT"])
    p.add_argument("--sma", type=int, nargs="+", default=[50, 100, 200])
    p.add_argument("--dca", type=float, default=100)
    p.add_argument("--yearly", type=int, help="also print year-by-year hold vs trend for this SMA")
    a = p.parse_args()
    closes = load(a.symbols)
    print(json.dumps(compare(closes, a.sma, a.dca), ensure_ascii=False, indent=2))
    if a.yearly:
        print(json.dumps(yearly(closes, a.yearly), indent=2))
