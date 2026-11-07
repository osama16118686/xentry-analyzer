"""Multi-coin portfolio backtest on one shared, compounding account.

Usage:
  python portfolio.py BTCUSDT ETHUSDT SOLUSDT --interval 1d --capital 40000 --risk 1 \
      --stop-atr 1.5 --target-atr 4.5 --entry pullback --log trades.csv

Long only, with the trend (EMA50 > EMA200 and close > SMA100). Every trade risks
`--risk`% of the account balance at that moment (realized profits and losses
included), at most one open trade per coin, and total open positions never exceed
the balance (no leverage). Entries fill at the next candle's open; a gap through
the stop exits at the open. If stop and target are both inside one candle, the
stop is assumed first. Fee and slippage are paid on entry and exit.

Entries:
  pullback  RSI crosses back above 40 (end of a dip)
  breakout  close above the previous 20-candle high
  trend     close crosses above SMA100 (start of a new trend)
"""
import argparse
import json

import numpy as np
import pandas as pd

from data import fetch_klines
from indicators import add_all, sma

ENTRIES = ["pullback", "breakout", "trend"]


def prepare(df, entry):
    d = add_all(df)
    d["sma100"] = sma(d["close"], 100)
    trend = (d["ema50"] > d["ema200"]) & (d["close"] > d["sma100"])
    if entry == "pullback":
        trig = (d["rsi"].shift() <= 40) & (d["rsi"] > 40)
    elif entry == "breakout":
        trig = d["close"] > d["high20"]
    elif entry == "trend":
        trig = (d["close"] > d["sma100"]) & (d["close"].shift() <= d["sma100"].shift())
    else:
        raise ValueError(entry)
    d["signal"] = trend & trig
    return d.iloc[200:]


def simulate(frames, capital, risk_pct, stop_atr, target_atr, fee_pct=0.1, slippage_pct=0.05):
    fee, slip = fee_pct / 100, slippage_pct / 100
    days = sorted(set().union(*[f.index for f in frames.values()]))
    cash, open_pos, trades, curve = capital, {}, [], []
    pending = {}  # coin -> signal candle's ATR, filled at next open
    for t in days:
        # 1) fill entries signalled on the previous candle
        for coin, a in list(pending.items()):
            f = frames[coin]
            if t not in f.index:
                continue
            o = f.at[t, "open"]
            entry = o * (1 + slip)
            stop, target = entry - stop_atr * a, entry + target_atr * a
            balance = cash + sum(p["qty"] * p["entry"] for p in open_pos.values())
            qty = balance * risk_pct / 100 / (entry - stop)
            qty = min(qty, cash / (entry * (1 + fee)))  # no leverage: only free cash
            if qty * entry > 1:
                cash -= qty * entry * (1 + fee)
                open_pos[coin] = {"entry": entry, "stop": stop, "target": target, "qty": qty,
                                  "time": t, "balance_before": balance}
            del pending[coin]
        # 2) exits
        for coin, p in list(open_pos.items()):
            f = frames[coin]
            if t not in f.index:  # the entry candle is checked too
                continue
            o, h, l = f.at[t, "open"], f.at[t, "high"], f.at[t, "low"]
            px = None
            if l <= p["stop"]:
                px, why = min(p["stop"], o), "stop"
            elif h >= p["target"]:
                px, why = max(p["target"], o), "target"
            if px is not None:
                px *= 1 - slip
                cash += p["qty"] * px * (1 - fee)
                pnl = p["qty"] * (px - p["entry"]) - p["qty"] * (p["entry"] + px) * fee
                trades.append({"coin": coin, "entry_time": f"{p['time']:%Y-%m-%d}", "exit_time": f"{t:%Y-%m-%d}",
                               "entry": round(p["entry"], 4), "exit": round(px, 4), "exit_reason": why,
                               "qty": round(p["qty"], 6), "position_usd": round(p["qty"] * p["entry"], 2),
                               "pnl_usd": round(pnl, 2), "r": round(pnl / (p["balance_before"] * risk_pct / 100), 2)})
                del open_pos[coin]
        # 3) new signals on this candle's close
        for coin, f in frames.items():
            if t in f.index and f.at[t, "signal"] and coin not in open_pos and coin not in pending:
                pending[coin] = f.at[t, "atr"]
        marked = cash + sum(p["qty"] * frames[c].at[t, "close"] for c, p in open_pos.items() if t in frames[c].index)
        curve.append((t, marked))
    # close anything still open at the last price
    for coin, p in open_pos.items():
        px = frames[coin]["close"].iloc[-1]
        pnl = p["qty"] * (px - p["entry"]) - p["qty"] * (p["entry"] + px) * fee
        trades.append({"coin": coin, "entry_time": f"{p['time']:%Y-%m-%d}", "exit_time": "open",
                       "entry": round(p["entry"], 4), "exit": round(px, 4), "exit_reason": "still open",
                       "qty": round(p["qty"], 6), "position_usd": round(p["qty"] * p["entry"], 2),
                       "pnl_usd": round(pnl, 2), "r": round(pnl / (p["balance_before"] * risk_pct / 100), 2)})
    eq = pd.Series(dict(curve))
    return eq, trades


def report(eq, trades, capital):
    rs = np.array([t["r"] for t in trades])
    streak = best = 0
    for r in rs:
        streak = streak + 1 if r <= 0 else 0
        best = max(best, streak)
    years = (eq.index[-1] - eq.index[0]).days / 365.25
    year_end = eq.groupby(eq.index.year).last()
    prev = year_end.shift().fillna(capital)
    yearly = {int(y): round((year_end[y] / prev[y] - 1) * 100, 1) for y in year_end.index}
    wins, losses = rs[rs > 0], rs[rs <= 0]
    return {
        "period": f"{eq.index[0]:%Y-%m-%d} → {eq.index[-1]:%Y-%m-%d}",
        "start_capital": capital,
        "final_balance": round(eq.iloc[-1], 2),
        "total_return_pct": round((eq.iloc[-1] / capital - 1) * 100, 1),
        "cagr_pct": round(((eq.iloc[-1] / capital) ** (1 / years) - 1) * 100, 1),
        "max_drawdown_pct": round((1 - eq / eq.cummax()).max() * 100, 1),
        "lowest_balance": round(eq.min(), 2),
        "trades": len(rs),
        "win_rate_pct": round(len(wins) / len(rs) * 100, 1) if len(rs) else 0,
        "avg_r": round(rs.mean(), 2) if len(rs) else 0,
        "profit_factor": round(wins.sum() / -losses.sum(), 2) if losses.sum() < 0 else None,
        "longest_losing_streak": best,
        "total_fees_and_pnl_usd": round(sum(t["pnl_usd"] for t in trades), 2),
        "yearly_return_pct": yearly,
    }


def load(symbols, interval, limit):
    return {s: fetch_klines(s, interval, limit) for s in symbols}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("symbols", nargs="*", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    p.add_argument("--interval", default="1d")
    p.add_argument("--limit", type=int, default=4000)
    p.add_argument("--capital", type=float, default=10000)
    p.add_argument("--risk", type=float, default=1.0)
    p.add_argument("--stop-atr", type=float, default=1.5)
    p.add_argument("--target-atr", type=float, default=4.5)
    p.add_argument("--entry", default="pullback", choices=ENTRIES)
    p.add_argument("--log", help="write every trade to this CSV")
    a = p.parse_args()
    raw = load(a.symbols, a.interval, a.limit)
    frames = {s: prepare(df, a.entry) for s, df in raw.items()}
    eq, trades = simulate(frames, a.capital, a.risk, a.stop_atr, a.target_atr)
    if a.log:
        pd.DataFrame(trades).to_csv(a.log, index=False)
    print(json.dumps(report(eq, trades, a.capital), ensure_ascii=False, indent=2))
