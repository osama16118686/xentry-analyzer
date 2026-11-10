"""Day-trading backtest on 1h candles: every trade opens and closes within the same UTC day.

Usage:
  python intraday.py BTCUSDT ETHUSDT SOLUSDT --capital 40000 --risk 1 --rr 2 --setup orb --limit 30000

Trades follow the daily trend known at the previous day's close: longs only when
daily EMA50 > EMA200 and close > SMA100, shorts only when the opposite holds
(`--sides long` disables shorts). One trade per coin per day. Each coin trades its
own equal share of the capital, compounding, risking `--risk`% of that share's
current balance. Anything still open is closed at the day's last candle close.
If a candle touches both stop and target, the stop counts. Costs both ways.

Setups:
  orb       range of the first 4 hourly candles; enter at the next open after a close
            beyond it, stop at the other side of the range
  vbreak    stop-entry at day open ± 0.5 × yesterday's range, stop at the day's open
  pullback  1h RSI crosses back above 40 (below 60 for shorts) with 1h EMA50 on the
            trend side; enter next open, stop 1.5 × 1h ATR
  evening   long from the 21:00 UTC open to the 23:00 UTC open (time-of-day effect);
            with --stop-atr 0 it holds the whole balance with no stop or target
Target is always `--rr` × the stop distance.
"""
import argparse
import json

import numpy as np
import pandas as pd

from data import fetch_klines
from indicators import atr, ema, rsi, sma

SETUPS = ["orb", "vbreak", "pullback", "evening"]


def daily_trend(h1):
    d = h1.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    c = d["close"]
    up = (ema(c, 50) > ema(c, 200)) & (c > sma(c, 100))
    down = (ema(c, 50) < ema(c, 200)) & (c < sma(c, 100))
    out = pd.DataFrame({"up": up, "down": down, "range": d["high"] - d["low"]})
    out = out.shift()  # known only after the day closed
    out.iloc[:200] = np.nan  # EMA200 warm-up
    return out


def run_coin(h1, setup, capital, risk_pct, rr, sides, fee_pct=0.1, slippage_pct=0.05,
             trend_filter=True, start=None, stop_atr=1.5):
    fee, slip = fee_pct / 100, slippage_pct / 100
    h1 = h1.copy()
    h1["rsi"], h1["ema50"], h1["atr"] = rsi(h1["close"]), ema(h1["close"], 50), atr(h1)
    trend = daily_trend(h1)
    balance, trades, curve = capital, [], []
    for day, g in h1.groupby(h1.index.floor("1D")):
        if day not in trend.index or pd.isna(trend.at[day, "up"]) or len(g) < 20:
            continue
        if start is not None and day < start:
            continue
        up, down = bool(trend.at[day, "up"]), bool(trend.at[day, "down"])
        if not trend_filter:
            up, down = True, True
        if setup == "evening":
            down = False
        if sides == "long":
            down = False
        if not (up or down):
            curve.append((day, balance))
            continue
        o, h, l, c = (g[k].to_numpy() for k in ("open", "high", "low", "close"))
        trade = None  # (side, entry_index, entry_price, stop, entry_on_candle)
        last = len(g) - 1  # exit at this candle's close if nothing hit
        exit_at_open = False
        if setup == "orb":
            hi, lo = h[:4].max(), l[:4].min()
            for i in range(4, len(g) - 1):
                if up and c[i] > hi:
                    trade = (1, i + 1, o[i + 1] * (1 + slip), lo, False)
                    break
                if down and c[i] < lo:
                    trade = (-1, i + 1, o[i + 1] * (1 - slip), hi, False)
                    break
        elif setup == "vbreak":
            k = 0.5 * trend.at[day, "range"]
            long_px, short_px = o[0] + k, o[0] - k
            for i in range(len(g)):
                if up and h[i] >= long_px:
                    trade = (1, i, max(long_px, o[i]) * (1 + slip), o[0], True)
                    break
                if down and l[i] <= short_px:
                    trade = (-1, i, min(short_px, o[i]) * (1 - slip), o[0], True)
                    break
        elif setup == "evening":
            hours = list(g.index.hour)
            if 21 in hours and 23 in hours and hours.index(21) > 0:
                i21, i23 = hours.index(21), hours.index(23)
                a = g["atr"].to_numpy()[i21 - 1]
                ent = o[i21] * (1 + slip)
                stop = ent - stop_atr * a if stop_atr else 0.0
                trade = (1, i21, ent, stop, False)
                last, exit_at_open = i23, True
        elif setup == "pullback":
            r, e, a = g["rsi"].to_numpy(), g["ema50"].to_numpy(), g["atr"].to_numpy()
            prev_r = h1["rsi"].shift().loc[g.index].to_numpy()
            for i in range(len(g) - 1):
                if up and prev_r[i] <= 40 < r[i] and c[i] > e[i]:
                    ent = o[i + 1] * (1 + slip)
                    trade = (1, i + 1, ent, ent - stop_atr * a[i], False)
                    break
                if down and prev_r[i] >= 60 > r[i] and c[i] < e[i]:
                    ent = o[i + 1] * (1 - slip)
                    trade = (-1, i + 1, ent, ent + stop_atr * a[i], False)
                    break
        if trade is None:
            curve.append((day, balance))
            continue
        side, j0, entry, stop, on_candle = trade
        dist = side * (entry - stop)
        if dist <= 0:
            curve.append((day, balance))
            continue
        if setup == "evening" and not stop_atr:
            # time-only trade: whole balance, no stop or target
            target, qty = np.inf, balance / entry
            r_unit = balance * risk_pct / 100
        else:
            target = entry + side * rr * dist
            qty = min(balance * risk_pct / 100 / dist, balance / entry)  # no leverage
            r_unit = balance * risk_pct / 100
        exit_px, why = None, "end of window" if exit_at_open else "end of day"
        for j in range(j0, last if exit_at_open else len(g)):
            hit_stop = l[j] <= stop if side == 1 else h[j] >= stop
            hit_tgt = h[j] >= target if side == 1 else l[j] <= target
            if hit_stop:
                gap_px = min(stop, o[j]) if side == 1 else max(stop, o[j])  # gaps fill at the open
                exit_px, why = (stop if on_candle and j == j0 else gap_px), "stop"
                break
            if hit_tgt and not (on_candle and j == j0):  # no same-candle target after a stop-entry
                exit_px, why = (max(target, o[j]) if side == 1 else min(target, o[j])), "target"
                break
        if exit_px is None:
            exit_px = o[last] if exit_at_open else c[last]
        exit_px *= 1 - side * slip
        pnl = side * qty * (exit_px - entry) - qty * (entry + exit_px) * fee
        r_mult = pnl / r_unit
        balance += pnl
        trades.append({"day": f"{day:%Y-%m-%d}", "side": "long" if side == 1 else "short",
                       "entry": round(entry, 4), "exit": round(exit_px, 4), "exit_reason": why,
                       "position_usd": round(qty * entry, 2), "pnl_usd": round(pnl, 2), "r": round(r_mult, 2)})
        curve.append((day, balance))
    return pd.Series(dict(curve)), trades


def summarize(eq, trades, capital):
    rs = np.array([t["r"] for t in trades]) if trades else np.array([])
    wins, losses = rs[rs > 0], rs[rs <= 0]
    streak = worst = 0
    for r in rs:
        streak = streak + 1 if r <= 0 else 0
        worst = max(worst, streak)
    years = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    return {
        "period": f"{eq.index[0]:%Y-%m-%d} → {eq.index[-1]:%Y-%m-%d}",
        "start_capital": round(capital, 2),
        "final_balance": round(eq.iloc[-1], 2),
        "total_return_pct": round((eq.iloc[-1] / capital - 1) * 100, 1),
        "cagr_pct": round(((eq.iloc[-1] / capital) ** (1 / years) - 1) * 100, 1),
        "max_drawdown_pct": round((1 - eq / eq.cummax()).max() * 100, 1),
        "trades": len(rs),
        "win_rate_pct": round(len(wins) / len(rs) * 100, 1) if len(rs) else 0,
        "avg_r": round(rs.mean(), 3) if len(rs) else 0,
        "profit_factor": round(wins.sum() / -losses.sum(), 2) if losses.sum() < 0 else None,
        "longest_losing_streak": worst,
        "exits": pd.Series([t["exit_reason"] for t in trades]).value_counts().to_dict(),
    }


def portfolio(data, setup, capital, risk_pct, rr, sides, fee_pct=0.1, slippage_pct=0.05, trend_filter=True,
              start=None, stop_atr=1.5):
    share = capital / len(data)
    curves, all_trades, per_coin = [], [], {}
    for sym, h1 in data.items():
        eq, tr = run_coin(h1, setup, share, risk_pct, rr, sides, fee_pct, slippage_pct, trend_filter, start, stop_atr)
        curves.append(eq)
        all_trades += [{**t, "coin": sym} for t in tr]
        per_coin[sym] = {"final": round(eq.iloc[-1], 2), "trades": len(tr)}
    eq = pd.concat(curves, axis=1).ffill().fillna(share).sum(axis=1)
    all_trades.sort(key=lambda t: t["day"])
    return eq, all_trades, per_coin


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("symbols", nargs="*", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    p.add_argument("--limit", type=int, default=30000, help="1h candles per coin")
    p.add_argument("--capital", type=float, default=10000)
    p.add_argument("--risk", type=float, default=1.0)
    p.add_argument("--rr", type=float, default=2.0)
    p.add_argument("--setup", default="orb", choices=SETUPS)
    p.add_argument("--sides", default="both", choices=["both", "long"])
    p.add_argument("--fee", type=float, default=0.1, help="fee per side %%")
    p.add_argument("--slippage", type=float, default=0.05, help="slippage per side %%")
    p.add_argument("--no-trend", action="store_true", help="trade every day, ignoring the daily trend")
    p.add_argument("--stop-atr", type=float, default=1.5, help="stop size for pullback / evening (0 = no stop)")
    p.add_argument("--start", help="first trading day, e.g. 2025-11-07 (earlier data only warms up)")
    p.add_argument("--log", help="write every trade to this CSV")
    a = p.parse_args()
    data = {s: fetch_klines(s, "1h", a.limit) for s in a.symbols}
    start = pd.Timestamp(a.start, tz="UTC") if a.start else None
    eq, trades, per_coin = portfolio(data, a.setup, a.capital, a.risk, a.rr, a.sides, a.fee, a.slippage,
                                     not a.no_trend, start, a.stop_atr)
    if a.log:
        pd.DataFrame(trades).to_csv(a.log, index=False)
    print(json.dumps({**summarize(eq, trades, a.capital), "per_coin": per_coin}, ensure_ascii=False, indent=2))
