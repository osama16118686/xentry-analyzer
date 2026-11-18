"""V2 PAPER TRACKER (no real orders, no keys). Run once after each 4h candle close.
Follows STRATEGY_V2_ADVANCED.md: ML (POC/ADX/OI filters, smart S/R target, BTC ETH SOL + XRP), daily breakout, 4h range,
strong-level fade with crowd contra. Also tracks the V2.1 candidate 'squeeze' separately (tag v21).
State: paper_v2.json. Public data only: Binance spot klines (data-api.binance.vision via data.py), OKX public rubik stats."""
import os, sys, json, time, subprocess, warnings
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
SK = os.path.join(HERE, "scripts")
sys.path.insert(0, SK)
import numpy as np, pandas as pd
from data import fetch_klines
from indicators import add_all

STATE = os.path.join(HERE, "paper_v2.json")
FEE, SLIP = 0.045/100, 0.02/100
ML_COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]
CORE = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
NOW = pd.Timestamp.now(tz="UTC")
log = []
def say(s): log.append(s)

def closed4h(sym, n=1000):
    d = add_all(fetch_klines(sym, "4h", n))
    if d.index[-1] + pd.Timedelta(hours=4) > NOW: d = d.iloc[:-1]
    return d
def okx(path):
    r = subprocess.run(["curl", "-s", "-m", "20", "https://www.okx.com" + path], capture_output=True, text=True)
    return json.loads(r.stdout)["data"]

def load():
    if os.path.exists(STATE): return json.load(open(STATE))
    return {"open": [], "pending": [], "closed": [], "last_candle": None, "last_day": None, "ml_streak": 0, "started": str(NOW)}
st = load()
D = {s: closed4h(s) for s in ML_COINS}
last_t = D["BTCUSDT"].index[-1]
if st["last_candle"] == str(last_t):
    print("ALREADY_PROCESSED", last_t); sys.exit(0)
prev_t = pd.Timestamp(st["last_candle"]) if st["last_candle"] else last_t

def pnl_of(p, px):
    side = p["side"]; px *= (1 - side*SLIP)
    return side*p["q"]*(px - p["e"]) - p["q"]*(p["e"] + px)*FEE

# ---------------- 1) update pending limits and open positions on candles after prev_t ----------------
def candles_after(sym, t0):
    d = D[sym]; return d[d.index > t0]
still_pending = []
for x in st["pending"]:
    d = candles_after(x["coin"], prev_t); filled = False
    for t, r in d.iterrows():
        x["age"] += 1
        if (r.low <= x["lim"]) if x["side"] == 1 else (r.high >= x["lim"]):
            e = (min(x["lim"], r.open) if x["side"] == 1 else max(x["lim"], r.open))*(1 + x["side"]*SLIP)
            if x["side"]*(e - x["stop"]) > 0:
                p = dict(x, e=e, q=x["risk"]/abs(e - x["stop"]), t0=str(t), bars=0); p.pop("lim"); p.pop("age")
                st["open"].append(p); say(f"FILLED {p['tag']} {p['strat']} {p['coin']} {'LONG' if p['side']==1 else 'SHORT'} @ {e:.4f} stop {p['stop']:.4f} tgt {p.get('tgt') or 'trail'} risk ${p['risk']:.0f}")
            filled = True; break
        if x["age"] >= 2: break
    if not filled and x["age"] < 2: still_pending.append(x)
    elif not filled: say(f"EXPIRED {x['tag']} {x['strat']} {x['coin']} limit {x['lim']:.4f}")
st["pending"] = still_pending

daily = {s: fetch_klines(s, "1d", 200) for s in CORE}
for s in CORE:
    if daily[s].index[-1] + pd.Timedelta(days=1) > NOW: daily[s] = daily[s].iloc[:-1]
still_open = []
for p in st["open"]:
    d = candles_after(p["coin"], prev_t); t0 = pd.Timestamp(p["t0"])
    d = d[d.index >= t0] if p.get("incl", False) else d[d.index > t0]
    side, px, why = p["side"], None, None
    for t, r in d.iterrows():
        p["bars"] += 1
        if (r.low <= p["stop"]) if side == 1 else (r.high >= p["stop"]):
            px = min(p["stop"], r.open) if side == 1 else max(p["stop"], r.open); why = "stop"; break
        if p.get("tgt") and ((r.high >= p["tgt"]) if side == 1 else (r.low <= p["tgt"])):
            px = max(p["tgt"], r.open) if side == 1 else min(p["tgt"], r.open); why = "target"; break
        if p["bars"] >= p["H"]: px = r.close; why = "time"; break
        if p.get("trail"):
            at = D[p["coin"]]["atr"].loc[t]
            if side == 1: p["peak"] = max(p.get("peak", p["e"]), r.high); p["stop"] = max(p["stop"], p["peak"] - p["trail"]*at)
            else: p["peak"] = min(p.get("peak", p["e"]), r.low); p["stop"] = min(p["stop"], p["peak"] + p["trail"]*at)
    if px is None and p["strat"] == "breakout":   # daily exit rule, checked on the last closed day
        x = daily[p["coin"]]; c = x.close.iloc[-1]; lo10 = x.low.iloc[-11:-1].min(); hi10 = x.high.iloc[-11:-1].max()
        if (c < lo10) if side == 1 else (c > hi10): px = D[p["coin"]].close.iloc[-1]; why = "10-day exit"
    if px is not None:
        v = pnl_of(p, px); R = v/p["risk"]
        st["closed"].append(dict(p, exit=px, why=why, pnl=v, R=R, t1=str(last_t)))
        if p["strat"] == "ML": st["ml_streak"] = st["ml_streak"] + 1 if R < -0.2 else (0 if R > 0.2 else st["ml_streak"])
        say(f"CLOSED {p['tag']} {p['strat']} {p['coin']} {'LONG' if side==1 else 'SHORT'} {why} @ {px:.4f} P&L ${v:+,.0f} ({R:+.2f}R)")
    else: still_open.append(p)
st["open"] = still_open

# ---------------- 2) new signals on the last closed candle ----------------
def busy(coin, strat, tag): return any(x["coin"] == coin and x["strat"] == strat and x["tag"] == tag for x in st["open"] + st["pending"])
def add_market(tag, strat, coin, side, stop, tgt, risk, H, trail=None, note=""):
    # enters at the next candle open: approximated by the last close (the next run checks exits from the next candle)
    e = D[coin].close.iloc[-1]*(1 + side*SLIP)
    if side*(e - stop) <= 0: return
    p = dict(tag=tag, strat=strat, coin=coin, side=side, e=e, stop=stop, tgt=tgt, risk=risk, q=risk/abs(e - stop), H=H, trail=trail, t0=str(last_t + pd.Timedelta(hours=4)), incl=True, bars=0, note=note)
    st["open"].append(p); say(f"NEW {tag} {strat} {coin} {'LONG' if side==1 else 'SHORT'} ~@ {e:.4f} stop {stop:.4f} tgt {tgt if tgt else 'trail '+str(trail)+'ATR'} risk ${risk:.0f} {note}")

def pivots(d, k=5):
    h, l = d.high, d.low
    ph = (h == h.rolling(2*k+1, center=True).max()); pl = (l == l.rolling(2*k+1, center=True).min())
    return ph.to_numpy(), pl.to_numpy()
def smart_rr(d, side):
    n = len(d); i = n - 1; c, at = d.close.iloc[i], d.atr.iloc[i]; ph, pl = pivots(d)
    js = range(max(0, i - 180), i - 5)
    if side == 1: cand = [d.high.iloc[j] for j in js if ph[j] and d.high.iloc[j] > c + 0.3*at]; dist = min(cand) - c if cand else None
    else: cand = [d.low.iloc[j] for j in js if pl[j] and d.low.iloc[j] < c - 0.3*at]; dist = c - max(cand) if cand else None
    return 1.5 if dist is None else float(np.clip(0.9*dist/(1.5*at), 0.75, 1.5))
def poc(sym, bins=50):
    d1 = fetch_klines(sym, "1h", 130); d1 = d1[d1.index + pd.Timedelta(hours=1) <= last_t + pd.Timedelta(hours=4)].iloc[-120:]
    H, L, V = d1.high.to_numpy(), d1.low.to_numpy(), d1.volume.to_numpy(); top, bot = H.max(), L.min()
    a = np.clip(((L-bot)/(top-bot)*bins).astype(int), 0, bins-1); b = np.clip(((H-bot)/(top-bot)*bins).astype(int), 0, bins-1)
    prof = np.zeros(bins)
    for x, y, v in zip(a, b, V): prof[x:y+1] += v/(y-x+1)
    edges = np.linspace(bot, top, bins+1); return ((edges[:-1]+edges[1:])/2)[prof.argmax()]
def oi_falling(sym):
    oi = okx(f"/api/v5/rubik/stat/contracts/open-interest-volume?ccy={sym[:-4]}&period=1H")
    return float(oi[0][1]) < float(oi[24][1])
def crowd_z(sym):
    ls = np.array([float(x[1]) for x in okx(f"/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy={sym[:-4]}&period=4H")][::-1])
    return (ls[-1] - ls.mean())/ls.std()
def ml_probs():
    out = {}
    cmds = [(["BTCUSDT", "ETHUSDT"], None), (["BTCUSDT", "ETHUSDT", "SOLUSDT"], "SOLUSDT"), (["BTCUSDT", "ETHUSDT", "XRPUSDT"], "XRPUSDT")]
    for syms, tr in cmds:
        cmd = ["timeout", "400", "python3", "ml_signals.py", "signal", *syms, "--threshold", "0.6"] + (["--trade", tr] if tr else [])
        r = subprocess.run(cmd, cwd=SK, capture_output=True, text=True)
        js = json.loads(r.stdout[r.stdout.index("{"):])
        out.update(js)
    return out

# ML engine
try:
    P = ml_probs(); ml_open = [x for x in st["open"] + st["pending"] if x["strat"] == "ML"]
    for s in ML_COINS:
        if s not in P or busy(s, "ML", "v2"): continue
        pr = P[s]; d = D[s]
        if pr["candle"][:13] != f"{last_t:%Y-%m-%d %H}":
            say(f"ML {s}: model candle {pr['candle']} != {last_t} (skipped)"); continue
        pl, ps = pr["p_long"], pr["p_short"]; side = 1 if (pl >= 0.6 and pl >= ps) else (-1 if ps >= 0.6 else 0)
        if not side: continue
        c, at = d.close.iloc[-1], d.atr.iloc[-1]; why = []
        if np.sign(c - d.ema200.iloc[-1]) != side: why.append("EMA200")
        if s != "XRPUSDT" and np.sign(c - poc(s)) != side: why.append("POC")
        if d.adx.iloc[-1] < 20: why.append("ADX<20")
        try:
            if not oi_falling(s): why.append("OI rising")
        except Exception: why.append("OI n/a")
        p_ = max(pl, ps)
        if why: say(f"ML {s} {'LONG' if side==1 else 'SHORT'} p={p_:.3f} filtered: {', '.join(why)}"); continue
        risk = 200 if p_ < 0.65 else (400 if p_ < 0.72 else 600)
        if st["ml_streak"] >= 3: risk *= 0.5
        if len(ml_open) >= 4 or sum(x["risk"] for x in ml_open) + risk > 1600: say(f"ML {s} skipped: cap"); continue
        rv = smart_rr(d, side)
        x = dict(tag="v2", strat="ML", coin=s, side=side, lim=c - side*0.25*at, stop=c - side*1.5*at, tgt=c + side*1.5*at*rv,
                 risk=risk, H=30 if rv < 1.75 else 60, trail=None, age=0, note=f"p={p_:.3f} rr={rv:.2f}")
        st["pending"].append(x); ml_open.append(x)
        say(f"NEW LIMIT v2 ML {s} {'LONG' if side==1 else 'SHORT'} limit {x['lim']:.4f} stop {x['stop']:.4f} target {x['tgt']:.4f} (1:{rv:.2f}) risk ${risk:.0f} p={p_:.3f}")
except Exception as e: say(f"ML error: {str(e)[:120]}")

# daily breakout (only when a new day closed)
try:
    day = str(daily["BTCUSDT"].index[-1])
    if st["last_day"] != day:
        st["last_day"] = day
        for s in CORE:
            if busy(s, "breakout", "v2"): continue
            x = daily[s]; tr = np.maximum(x.high - x.low, np.maximum(abs(x.high - x.close.shift()), abs(x.low - x.close.shift())))
            a = tr.rolling(20).mean().iloc[-1]; c = x.close.iloc[-1]; e100 = x.close.ewm(span=100, adjust=False).mean().iloc[-1]
            hi20, lo20 = x.high.iloc[-21:-1].max(), x.low.iloc[-21:-1].min()
            side = 1 if c > hi20 else (-1 if c < lo20 else 0)
            if side and np.sign(c - e100) == side:
                add_market("v2", "breakout", s, side, c - side*2*a, None, 200, 9999, note="daily 20-day breakout")
except Exception as e: say(f"breakout error: {str(e)[:120]}")

# 4h range mean-reversion
try:
    for s in CORE:
        if busy(s, "range", "v2"): continue
        d = D[s]; i = len(d) - 1; hh = d.high.iloc[i-30:i].max(); ll = d.low.iloc[i-30:i].min(); w = hh - ll
        r = d.iloc[i]; side = 0
        if r.adx < 20 and w < 8*r.atr:
            if r.low <= ll + 0.1*w and r.close > r.open and r.close > ll: side = 1
            if r.high >= hh - 0.1*w and r.close < r.open and r.close < hh: side = -1
        if side:
            stop = ll - r.atr if side == 1 else hh + r.atr; tgt = (hh + ll)/2
            if side*(tgt - r.close) > 0: add_market("v2", "range", s, side, stop, tgt, 200, 30)
except Exception as e: say(f"range error: {str(e)[:120]}")

# strong-level fade with crowd contra
try:
    for s in CORE:
        if busy(s, "levels", "v2"): continue
        d = D[s]; i = len(d) - 1; a = d.atr.iloc[i]; ph, pl = pivots(d)
        his = [d.high.iloc[j] for j in range(i-360, i) if ph[j] and j + 5 <= i - 1]
        los = [d.low.iloc[j] for j in range(i-360, i) if pl[j] and j + 5 <= i - 1]
        r, rp = d.iloc[i], d.iloc[i-1]; side, lev = 0, None
        for lv in sorted(set(his), reverse=True):
            cl = [p for p in his if abs(p - lv) <= 0.5*a]
            if len(cl) >= 3 and r.high >= lv - 0.2*a and r.close < lv and rp.close < lv and r.close < r.open: side, lev = -1, max(cl); break
        if not side:
            for lv in sorted(set(los)):
                cl = [p for p in los if abs(p - lv) <= 0.5*a]
                if len(cl) >= 3 and r.low <= lv + 0.2*a and r.close > lv and rp.close > lv and r.close > r.open: side, lev = 1, min(cl); break
        if side:
            z = crowd_z(s)
            if side*z < 0:
                e = r.close; add_market("v2", "levels", s, side, lev - a if side == 1 else lev + a, e*(1 + side*0.04), 200, 30, note=f"level {lev:.4f} crowd z {z:+.2f}")
            else: say(f"levels {s} {'LONG' if side==1 else 'SHORT'} at {lev:.4f} skipped: crowd z {z:+.2f} not contra")
except Exception as e: say(f"levels error: {str(e)[:120]}")

# V2.1 candidate: squeeze breakout with 3-ATR trailing stop (tracked separately)
try:
    for s in CORE:
        if busy(s, "squeeze", "v21"): continue
        d = D[s]; c = d.close; bw = 4*c.rolling(20).std()/c.rolling(20).mean()
        thr = bw.rolling(540, min_periods=180).quantile(0.15)
        if not (bw.iloc[-2] <= thr.iloc[-2]): continue
        hh, ll = d.high.iloc[-21:-1].max(), d.low.iloc[-21:-1].min()
        side = 1 if c.iloc[-1] > hh else (-1 if c.iloc[-1] < ll else 0)
        if side: add_market("v21", "squeeze", s, side, c.iloc[-1] - side*1.5*d.atr.iloc[-1], None, 200, 60, trail=3.0)
except Exception as e: say(f"squeeze error: {str(e)[:120]}")

st["last_candle"] = str(last_t)
json.dump(st, open(STATE, "w"), indent=1, default=str)

# ---------------- 3) report ----------------
print(f"V2 PAPER @ candle {last_t:%Y-%m-%d %H:%M} UTC (started {st['started'][:16]})")
for l in log: print(" ", l)
if not log: print("  no new events")
def mark(p):
    px = D[p["coin"]].close.iloc[-1]; return pnl_of(p, px)
print("OPEN:", "none" if not st["open"] else "")
for p in st["open"]: print(f"  {p['tag']} {p['strat']} {p['coin']} {'LONG' if p['side']==1 else 'SHORT'} e {p['e']:.4f} stop {p['stop']:.4f} tgt {p.get('tgt') or 'trail'} unreal ${mark(p):+,.0f}")
for x in st["pending"]: print(f"  PENDING {x['tag']} {x['strat']} {x['coin']} limit {x['lim']:.4f}")
cl = pd.DataFrame(st["closed"])
for tag in ("v2", "v21"):
    c_ = cl[cl.tag == tag] if len(cl) else cl
    n = len(c_); net = c_.pnl.sum() if n else 0; w = (c_.pnl > 0).mean()*100 if n else 0
    unreal = sum(mark(p) for p in st["open"] if p["tag"] == tag)
    print(f"TOTAL {tag}: closed {n} win {w:.0f}% net ${net:+,.0f} | open unreal ${unreal:+,.0f}")
