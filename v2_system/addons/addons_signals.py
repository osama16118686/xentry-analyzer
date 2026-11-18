"""V2.2 add-ons: daily signals (info / paper only, no orders, no keys).
Run once a day, after the daily candle closes (00:00 UTC), from inside the V2_system folder:
    python3 addons_signals.py [capital]
Prints:
  1) the daily ML signal on BTC/ETH/SOL (threshold 0.6, daily EMA200 filter, stop and target 1.5 daily ATR, max 10 days)
  2) the gold (PAXG) daily breakout (20-day high/low + daily EMA100, stop 2 ATR(20), exit on the 10-day opposite level)
  3) a reminder of the total open-risk cap (about 5.2% of capital = $2,400 on $46k).
Risk is $200 per trade on $46k, scaled by capital / 46,000."""
import os, sys, json, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "scripts")
sys.path.insert(0, SK)
import pandas as pd
from data import fetch_klines

CAP = float(sys.argv[1]) if len(sys.argv) > 1 else 46000.0
SCALE = CAP / 46000.0
RISK = 200 * SCALE
NOW = pd.Timestamp.now(tz="UTC")

def closed_daily(sym, n=400):
    d = fetch_klines(sym, "1d", n)
    if d.index[-1] + pd.Timedelta(days=1) > NOW: d = d.iloc[:-1]
    return d

def atr(d, n):
    tr = pd.concat([d.high - d.low, (d.high - d.close.shift()).abs(), (d.low - d.close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

print(f"V2.2 ADD-ONS  capital ${CAP:,.0f}  risk per trade ${RISK:,.0f}")

# 1) daily ML
print("\n1) Daily ML (BTC ETH SOL)")
try:
    r = subprocess.run(["python3", "ml_signals.py", "signal", "BTCUSDT", "ETHUSDT", "SOLUSDT", "--interval", "1d",
                        "--limit", "3000", "--threshold", "0.6", "--horizon", "10"], cwd=SK, capture_output=True, text=True, timeout=900)
    plans = json.loads(r.stdout[r.stdout.index("{"):])
    for s, p in plans.items():
        d = closed_daily(s, 400); c = d.close
        e200 = c.ewm(span=200, adjust=False).mean().iloc[-1]; a = atr(d, 14).iloc[-1]; px = c.iloc[-1]
        line = f"  {s}: p_long {p['p_long']:.3f} p_short {p['p_short']:.3f}  close {px:,.4f}  EMA200d {e200:,.4f}"
        side = 1 if p["action"] == "BUY" else -1 if p["action"].startswith("SELL") else 0
        if not side: print(line + "  -> no signal"); continue
        if (side == 1 and px <= e200) or (side == -1 and px >= e200):
            print(line + "  -> signal FILTERED by daily EMA200"); continue
        stop, tgt = px - side*1.5*a, px + side*1.5*a; q = RISK / (1.5*a)
        print(line + f"\n     -> {'LONG' if side == 1 else 'SHORT'} at next daily open (market). stop {stop:,.4f} target {tgt:,.4f}"
              f" qty {q:,.4f} (${q*px:,.0f}) risk ${RISK:,.0f}. Close after 10 days if neither is hit.")
except Exception as e:
    print("  daily ML unavailable:", str(e)[:150])

# 2) gold breakout
print("\n2) Gold (PAXGUSDT) daily breakout")
try:
    d = closed_daily("PAXGUSDT", 400); c = d.close
    e100 = c.ewm(span=100, adjust=False).mean().iloc[-1]; a20 = atr(d, 20).iloc[-1]
    hh, ll = d.high.iloc[-21:-1].max(), d.low.iloc[-21:-1].min()
    h10, l10 = d.high.iloc[-11:-1].max(), d.low.iloc[-11:-1].min()
    px = c.iloc[-1]
    print(f"  close {px:,.2f}  20d high {hh:,.2f}  20d low {ll:,.2f}  EMA100d {e100:,.2f}  ATR20 {a20:,.2f}")
    side = 1 if (px > hh and px > e100) else -1 if (px < ll and px < e100) else 0
    if side:
        stop = px - side*2*a20; q = RISK / (2*a20)
        print(f"  -> {'LONG' if side == 1 else 'SHORT'} at next daily open. stop {stop:,.2f} qty {q:,.4f} (${q*px:,.0f}) risk ${RISK:,.0f}")
    else:
        print("  -> no breakout")
    print(f"  exit rule for an open gold trade: LONG closes if a daily close < {l10:,.2f}; SHORT closes if a daily close > {h10:,.2f} (exit at next open), or the stop.")
except Exception as e:
    print("  gold unavailable:", str(e)[:150])

print(f"\n3) Open-risk cap: skip ANY new signal (all strategies) if total open risk would exceed ${2400*SCALE:,.0f}.")
print("\nInfo / paper only. Not financial advice.")
