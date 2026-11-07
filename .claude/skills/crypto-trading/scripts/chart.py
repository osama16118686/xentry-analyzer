"""Candlestick chart with EMAs, support/resistance and past strategy signals with outcomes.

Usage:
  python chart.py BTCUSDT --interval 4h --bars 360 --out btc_4h.png
"""
import argparse

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backtest import run
from data import get_data
from indicators import add_all, swing_levels


def draw(df, symbol, interval, bars, strategy, out):
    d = add_all(df)
    supports, resistances = swing_levels(df)
    result = run(df, strategy, keep_trades=10_000)
    v = d.iloc[-bars:]
    x = np.arange(len(v))
    pos = {t: i for i, t in enumerate(v.index)}
    a = d["atr"].iloc[-1]

    fig, ax = plt.subplots(figsize=(16, 8), dpi=110)
    up = v["close"] >= v["open"]
    col = np.where(up, "#26a69a", "#ef5350")
    ax.vlines(x, v["low"], v["high"], color=col, linewidth=0.8)
    ax.bar(x, (v["close"] - v["open"]).abs().clip(lower=a * 0.02), bottom=np.minimum(v["open"], v["close"]),
           color=col, width=0.7)
    ax.plot(x, v["ema50"], color="orange", lw=1.4, label="EMA 50")
    ax.plot(x, v["ema200"], color="#2962ff", lw=1.6, label="EMA 200")

    for lv in supports:
        ax.axhspan(lv - a * 0.25, lv + a * 0.25, color="#26a69a", alpha=0.15)
        ax.axhline(lv, color="#26a69a", lw=1, ls="--")
        ax.text(len(v) + 1, lv, f"Support {lv:,.0f}", color="#1b7f74", va="center", fontsize=9, weight="bold")
    for lv in resistances:
        ax.axhspan(lv - a * 0.25, lv + a * 0.25, color="#ef5350", alpha=0.12)
        ax.axhline(lv, color="#ef5350", lw=1, ls="--")
        ax.text(len(v) + 1, lv, f"Resistance {lv:,.0f}", color="#c62828", va="center", fontsize=9, weight="bold")

    shown = []
    for t in result["last_trades"]:
        ti, to = pd.Timestamp(t["entry_time"]), pd.Timestamp(t["exit_time"])
        if ti not in pos:
            continue
        i = pos[ti]
        j = pos.get(to, len(v) - 1)
        win = t["r"] > 0
        long = t["side"] == "long"
        ax.plot([i, j], [t["entry"], t["exit"]], color="#2e7d32" if win else "#c62828", lw=1.5, ls=":")
        ax.scatter(i, t["entry"], marker="^" if long else "v", s=140, zorder=5,
                   color="#00c853" if long else "#d50000", edgecolor="black")
        ax.scatter(j, t["exit"], marker="o", s=60, zorder=5, color="#2e7d32" if win else "#c62828")
        ax.annotate(f"{'BUY' if long else 'SELL'}\n{t['r']:+.2f}R", (i, t["entry"]),
                    xytext=(0, -38 if long else 26), textcoords="offset points", ha="center", fontsize=8,
                    weight="bold", color="#2e7d32" if win else "#c62828")
        shown.append(t)

    step = max(1, len(v) // 10)
    ax.set_xticks(x[::step])
    ax.set_xticklabels([t.strftime("%m-%d") for t in v.index[::step]])
    ax.set_xlim(-2, len(v) + 14)
    ax.grid(alpha=0.2)
    ax.legend(loc="upper left")
    wins = sum(t["r"] > 0 for t in shown)
    ax.set_title(f"{symbol} {interval} | last close {v['close'].iloc[-1]:,.2f} | {v.index[-1]:%Y-%m-%d %H:%M} UTC | "
                 f"{strategy} signals on chart: {len(shown)} ({wins} won, {len(shown) - wins} lost)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out)
    return shown, supports, resistances, result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("symbol", nargs="?", default="BTCUSDT")
    p.add_argument("--interval", default="4h")
    p.add_argument("--bars", type=int, default=360)
    p.add_argument("--limit", type=int, default=2000)
    p.add_argument("--strategy", default="confluence")
    p.add_argument("--csv")
    p.add_argument("--out", default="chart.png")
    a = p.parse_args()
    df = get_data(a.symbol, a.interval, a.csv, a.limit)
    shown, sup, res, _ = draw(df, a.symbol, a.interval, a.bars, a.strategy, a.out)
    print(f"supports={sup} resistances={res}")
    for t in shown:
        print(t)
