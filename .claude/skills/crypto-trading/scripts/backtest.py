"""Backtest long-only (spot) strategies with fees, slippage and fixed-risk sizing.

Usage:
  python backtest.py ETHUSDT --interval 4h --strategy trend_pullback
  python backtest.py --csv eth_4h.csv --strategy all --split 0.7

The --split option reports in-sample and out-of-sample results separately. A strategy
that only works in-sample is overfitted and must not be used.
"""
import argparse
import json

import numpy as np

from data import get_data
from indicators import add_all


def signals(d, name):
    """Boolean Series: enter long at the NEXT candle's open when True."""
    if name == "trend_pullback":
        # Uptrend, RSI dipped below 40 and crosses back above it
        return (d["ema50"] > d["ema200"]) & (d["rsi"].shift() < 40) & (d["rsi"] >= 40)
    if name == "breakout":
        # Close above previous 20-candle high on 1.5x average volume, in an uptrend
        return (d["close"] > d["high20"]) & (d["vol_ratio"] > 1.5) & (d["close"] > d["ema200"])
    if name == "mean_reversion":
        # Oversold close below lower Bollinger band, not in a crash below EMA200 by >15%
        return (d["close"] < d["bb_lower"]) & (d["rsi"] < 30) & (d["close"] > d["ema200"] * 0.85)
    raise ValueError(f"استراتيجية غير معروفة: {name}")


STRATEGIES = ["trend_pullback", "breakout", "mean_reversion"]


def run(df, strategy, stop_atr=1.5, target_atr=3.0, risk_pct=1.0, fee_pct=0.1, slippage_pct=0.05):
    d = add_all(df).iloc[200:]  # skip EMA200 warm-up
    sig = signals(d, strategy).to_numpy()
    o, h, l, c = (d[k].to_numpy() for k in ("open", "high", "low", "close"))
    atr_v = d["atr"].to_numpy()
    fee, slip = fee_pct / 100, slippage_pct / 100

    equity, peak, max_dd = 1.0, 1.0, 0.0
    trades = []
    i = 0
    while i < len(d) - 1:
        if not sig[i]:
            i += 1
            continue
        entry = o[i + 1] * (1 + slip)
        stop = entry - stop_atr * atr_v[i]
        target = entry + target_atr * atr_v[i]
        qty = equity * risk_pct / 100 / (entry - stop)
        qty = min(qty, equity / entry)  # spot: no leverage
        exit_price, j = None, i + 1
        while j < len(d):
            # If both stop and target are inside one candle, assume the stop hit first
            if l[j] <= stop:
                exit_price = min(stop, o[j]) * (1 - slip)
                break
            if h[j] >= target:
                exit_price = max(target, o[j]) * (1 - slip)
                break
            j += 1
        if exit_price is None:  # still open at end of data
            j = len(d) - 1
            exit_price = c[j]
        pnl = qty * (exit_price - entry) - qty * (entry + exit_price) * fee
        r_multiple = pnl / (equity * risk_pct / 100)
        equity += pnl
        peak = max(peak, equity)
        max_dd = max(max_dd, 1 - equity / peak)
        trades.append({"entry_time": str(d.index[i + 1]), "exit_time": str(d.index[j]),
                       "entry": round(entry, 4), "exit": round(exit_price, 4), "r": round(r_multiple, 2)})
        i = j + 1

    rs = np.array([t["r"] for t in trades])
    wins, losses = rs[rs > 0], rs[rs <= 0]
    return {
        "strategy": strategy,
        "period": f"{d.index[0]} → {d.index[-1]}",
        "trades": len(trades),
        "win_rate_pct": round(len(wins) / len(rs) * 100, 1) if len(rs) else 0,
        "avg_r": round(rs.mean(), 2) if len(rs) else 0,
        "profit_factor": round(wins.sum() / -losses.sum(), 2) if len(losses) and losses.sum() < 0 else None,
        "total_return_pct": round((equity - 1) * 100, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "buy_and_hold_pct": round((c[-1] / o[0] - 1) * 100, 2),
        "last_trades": trades[-5:],
        "reliable": len(trades) >= 30,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("symbol", nargs="?", default="ETHUSDT")
    p.add_argument("--interval", default="4h")
    p.add_argument("--csv")
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--strategy", default="all", choices=STRATEGIES + ["all"])
    p.add_argument("--stop-atr", type=float, default=1.5)
    p.add_argument("--target-atr", type=float, default=3.0)
    p.add_argument("--risk", type=float, default=1.0)
    p.add_argument("--fee", type=float, default=0.1)
    p.add_argument("--split", type=float, help="نسبة البيانات للفترة الأولى، مثل 0.7")
    a = p.parse_args()

    df = get_data(a.symbol, a.interval, a.csv, a.limit)
    names = STRATEGIES if a.strategy == "all" else [a.strategy]
    kw = dict(stop_atr=a.stop_atr, target_atr=a.target_atr, risk_pct=a.risk, fee_pct=a.fee)
    results = []
    for name in names:
        if a.split:
            cut = int(len(df) * a.split)
            # Out-of-sample keeps 200 earlier candles for indicator warm-up
            results.append({"in_sample": run(df.iloc[:cut], name, **kw),
                            "out_of_sample": run(df.iloc[max(cut - 200, 0):], name, **kw)})
        else:
            results.append(run(df, name, **kw))
    print(json.dumps(results, ensure_ascii=False, indent=2))
