"""Machine-learning trade signals: entry, stop, target and size, tested walk-forward.

A gradient-boosting model learns, from past candles only, the probability that a
trade (stop = 1.5 ATR, target = rr x stop) reaches its target before its stop within
`--horizon` candles. It trades only when that probability is at least `--threshold`.

Usage:
  python ml_signals.py backtest BTCUSDT ETHUSDT SOLUSDT --interval 4h --rr 1 --capital 40000
  python ml_signals.py signal   BTCUSDT ETHUSDT SOLUSDT --interval 4h --rr 1 --capital 40000

backtest: walk-forward. Each month the model is retrained on every trade whose
          outcome was already known before that month, then predicts that month.
signal:   trains on all known history and prints today's plan for each coin.

Simulation: entry at the next candle's open, one trade per coin at a time, each coin
trades an equal share of the capital, 1% risk of that share's current balance, no
leverage, costs on entry and exit, stop assumed first if both are hit in one candle.
"""
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from data import fetch_klines
from indicators import add_all


def features(df, btc):
    d = add_all(df)
    c, a = d["close"], d["atr"]
    f = pd.DataFrame(index=d.index)
    for k in (1, 3, 6, 12, 24, 48):
        f[f"ret_{k}"] = np.log(c / c.shift(k))
    for k in (6, 24):
        f[f"btc_ret_{k}"] = np.log(btc["close"] / btc["close"].shift(k)).reindex(d.index)
    f["rsi"] = d["rsi"]
    f["macd_hist"] = d["macd_hist"] / a
    f["adx"] = d["adx"]
    f["atr_pct"] = a / c
    f["vol_regime"] = a / a.rolling(120).mean()
    f["bb_pos"] = (c - d["bb_lower"]) / (d["bb_upper"] - d["bb_lower"])
    for n in (20, 50, 200):
        f[f"dist_ema{n}"] = (c - d[f"ema{n}"]) / a
    f["ema50_gt_200"] = (d["ema50"] > d["ema200"]).astype(int)
    f["vol_ratio"] = d["vol_ratio"]
    f["dist_high20"] = (d["high"].rolling(20).max() - c) / a
    f["dist_low20"] = (c - d["low"].rolling(20).min()) / a
    f["hour"] = d.index.hour
    f["dow"] = d.index.dayofweek
    return d, f


def labels(d, side, stop_atr, rr, horizon):
    """1 if a trade entered at the next open hits target before stop within horizon."""
    o, h, l = (d[k].to_numpy() for k in ("open", "high", "low"))
    a = d["atr"].to_numpy()
    n = len(d)
    y = np.full(n, np.nan)
    for t in range(n - horizon - 1):
        entry = o[t + 1]
        stop = entry - side * stop_atr * a[t]
        target = entry + side * rr * stop_atr * a[t]
        out = 0.0
        for j in range(t + 1, t + 1 + horizon):
            if (l[j] <= stop) if side == 1 else (h[j] >= stop):
                break
            if (h[j] >= target) if side == 1 else (l[j] <= target):
                out = 1.0
                break
        y[t] = out
    return y


def model():
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=200,
                                          l2_regularization=1.0, min_samples_leaf=200, random_state=0)


def build(raw, stop_atr, rr, horizon):
    btc = raw.get("BTCUSDT", next(iter(raw.values())))
    rows = []
    for sym, df in raw.items():
        d, f = features(df, btc)
        f["coin"] = sym
        f["y_long"] = labels(d, 1, stop_atr, rr, horizon)
        f["y_short"] = labels(d, -1, stop_atr, rr, horizon)
        f["known_at"] = d.index.to_series().shift(-(horizon + 1))  # outcome known by then
        rows.append((sym, d, f.iloc[200:]))  # EMA200 warm-up
    return rows


def walk_forward(rows, start, min_train_years=2.0):
    allf = pd.concat([f for _, _, f in rows])
    cols = [c for c in allf.columns if c not in ("coin", "y_long", "y_short", "known_at")]
    first = allf.index.min() + pd.Timedelta(days=365 * min_train_years)
    months = pd.date_range(max(first, start), allf.index.max(), freq="MS", tz="UTC")
    preds = []
    for m0, m1 in zip(months, list(months[1:]) + [allf.index.max() + pd.Timedelta(hours=1)]):
        train = allf[(allf["known_at"] < m0) & allf["known_at"].notna()]
        test = allf[(allf.index >= m0) & (allf.index < m1)]
        if len(test) == 0 or len(train) < 2000:
            continue
        out = test[["coin"]].copy()
        for side in ("long", "short"):
            y = train[f"y_{side}"]
            mdl = model().fit(train[cols], y)
            out[f"p_{side}"] = mdl.predict_proba(test[cols])[:, 1]
        preds.append(out)
    return pd.concat(preds), cols


def simulate(d, p, capital, threshold, stop_atr, rr, horizon, risk_pct=1.0, fee_pct=0.045, slippage_pct=0.02):
    fee, slip = fee_pct / 100, slippage_pct / 100
    d = d.loc[p.index.min():]
    p = p.reindex(d.index)
    o, h, l, c, a = (d[k].to_numpy() for k in ("open", "high", "low", "close", "atr"))
    pl, ps = p["p_long"].to_numpy(), p["p_short"].to_numpy()
    bal, trades, curve, i = capital, [], [], 0
    while i < len(d) - 1:
        side = 0
        if pl[i] >= threshold and pl[i] >= ps[i]:
            side = 1
        elif ps[i] >= threshold:
            side = -1
        if side == 0 or np.isnan(pl[i]):
            curve.append((d.index[i], bal))
            i += 1
            continue
        entry = o[i + 1] * (1 + side * slip)
        dist = stop_atr * a[i]
        stop, target = entry - side * dist, entry + side * rr * dist
        qty = min(bal * risk_pct / 100 / dist, bal / entry)
        px, why, j = None, "time", i + 1
        for j in range(i + 1, min(i + 1 + horizon, len(d))):
            if (l[j] <= stop) if side == 1 else (h[j] >= stop):
                px, why = (min(stop, o[j]) if side == 1 else max(stop, o[j])), "stop"
                break
            if (h[j] >= target) if side == 1 else (l[j] <= target):
                px, why = (max(target, o[j]) if side == 1 else min(target, o[j])), "target"
                break
        if px is None:
            px = c[j]
        px *= 1 - side * slip
        pnl = side * qty * (px - entry) - qty * (entry + px) * fee
        trades.append({"time": f"{d.index[i + 1]:%Y-%m-%d %H:%M}", "side": "long" if side == 1 else "short",
                       "prob": round(float(pl[i] if side == 1 else ps[i]), 3), "entry": round(entry, 4),
                       "stop": round(stop, 4), "target": round(target, 4), "exit": round(px, 4), "exit_reason": why,
                       "pnl_usd": round(pnl, 2), "r": round(pnl / (bal * risk_pct / 100), 2)})
        bal += pnl
        curve.append((d.index[j], bal))
        i = j + 1
    return pd.Series(dict(curve)), trades


def summary(curves, trades, capital):
    eq = pd.concat(curves, axis=1).sort_index().ffill().bfill().sum(axis=1)
    rs = np.array([t["r"] for t in trades])
    wins, losses = rs[rs > 0], rs[rs <= 0]
    return {"final_balance": round(eq.iloc[-1], 2), "total_return_pct": round((eq.iloc[-1] / capital - 1) * 100, 1),
            "max_drawdown_pct": round((1 - eq / eq.cummax()).max() * 100, 1), "trades": len(rs),
            "win_rate_pct": round(len(wins) / len(rs) * 100, 1) if len(rs) else 0,
            "avg_r": round(rs.mean(), 3) if len(rs) else 0,
            "profit_factor": round(wins.sum() / -losses.sum(), 2) if len(losses) and losses.sum() < 0 else None}


def backtest(raw, capital, thresholds, stop_atr, rr, horizon, start, fee, slip):
    rows = build(raw, stop_atr, rr, horizon)
    preds, _ = walk_forward(rows, start)
    allf = pd.concat([f for _, _, f in rows])
    test_rows = allf.loc[allf.index >= preds.index.min()]
    base = {"base_rate_long_pct": round(test_rows["y_long"].mean() * 100, 1),
            "base_rate_short_pct": round(test_rows["y_short"].mean() * 100, 1)}
    out = {"tested": f"{preds.index.min():%Y-%m-%d} → {preds.index.max():%Y-%m-%d}", **base, "by_threshold": {}}
    share = capital / len(rows)
    for thr in thresholds:
        curves, trades = [], []
        for sym, d, _ in rows:
            p = preds[preds["coin"] == sym][["p_long", "p_short"]]
            eq, tr = simulate(d, p, share, thr, stop_atr, rr, horizon, fee_pct=fee, slippage_pct=slip)
            curves.append(eq)
            trades += [{**t, "coin": sym} for t in tr]
        out["by_threshold"][thr] = summary(curves, trades, capital)
    return out


def signal(raw, capital, threshold, stop_atr, rr, horizon):
    rows = build(raw, stop_atr, rr, horizon)
    allf = pd.concat([f for _, _, f in rows])
    cols = [c for c in allf.columns if c not in ("coin", "y_long", "y_short", "known_at")]
    train = allf[allf["y_long"].notna()]
    mdl = {s: model().fit(train[cols], train[f"y_{s}"]) for s in ("long", "short")}
    plans = {}
    share = capital / len(rows)
    for sym, d, f in rows:
        x = f[cols].iloc[[-1]]
        pl, ps = (float(mdl[s].predict_proba(x)[0, 1]) for s in ("long", "short"))
        price, a = d["close"].iloc[-1], d["atr"].iloc[-1]
        plan = {"candle": f"{d.index[-1]:%Y-%m-%d %H:%M} UTC", "price": round(price, 4),
                "p_long": round(pl, 3), "p_short": round(ps, 3), "action": "no trade"}
        side = 1 if pl >= threshold and pl >= ps else -1 if ps >= threshold else 0
        if side:
            dist = stop_atr * a
            qty = min(share * 0.01 / dist, share / price)
            plan.update({"action": "BUY" if side == 1 else "SELL (short)", "entry": round(price, 4),
                         "stop": round(price - side * dist, 4), "target": round(price + side * rr * dist, 4),
                         "quantity": round(qty, 6), "position_usd": round(qty * price, 2),
                         "risk_usd": round(qty * dist, 2), "max_hold_candles": horizon})
        plans[sym] = plan
    return plans


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["backtest", "signal"])
    p.add_argument("symbols", nargs="*", default=["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    p.add_argument("--interval", default="4h")
    p.add_argument("--limit", type=int, default=15000)
    p.add_argument("--capital", type=float, default=40000)
    p.add_argument("--rr", type=float, default=1.0)
    p.add_argument("--stop-atr", type=float, default=1.5)
    p.add_argument("--horizon", type=int, default=30, help="max candles to hold")
    p.add_argument("--threshold", type=float, nargs="+", default=[0.5, 0.55, 0.6, 0.65, 0.7])
    p.add_argument("--start", default="2022-01-01")
    p.add_argument("--fee", type=float, default=0.045, help="fee per side %% (futures taker with BNB)")
    p.add_argument("--slippage", type=float, default=0.02)
    a = p.parse_args()
    raw = {s: fetch_klines(s, a.interval, a.limit) for s in a.symbols}
    if a.mode == "backtest":
        res = backtest(raw, a.capital, a.threshold, a.stop_atr, a.rr, a.horizon,
                       pd.Timestamp(a.start, tz="UTC"), a.fee, a.slippage)
    else:
        # decide only on closed candles, as in the backtest
        now = pd.Timestamp.now(tz="UTC")
        raw = {s: df if df.index[-1] + pd.Timedelta(a.interval) <= now else df.iloc[:-1] for s, df in raw.items()}
        res = signal(raw, a.capital, a.threshold[0], a.stop_atr, a.rr, a.horizon)
    print(json.dumps(res, ensure_ascii=False, indent=2))
