"""Technical snapshot of a coin for one timeframe.

Usage:
  python analyze.py ETHUSDT --interval 4h
  python analyze.py --csv eth_4h.csv
"""
import argparse
import json

from data import get_data
from indicators import add_all, swing_levels


def analyze(df):
    d = add_all(df)
    last = d.iloc[-1]
    price, a = last["close"], last["atr"]

    # Trend and momentum score from -5 (very bearish) to +5 (very bullish)
    checks = {
        "price_above_ema50": price > last["ema50"],
        "price_above_ema200": price > last["ema200"],
        "ema50_above_ema200": last["ema50"] > last["ema200"],
        "macd_above_signal": last["macd"] > last["macd_signal"],
        "rsi_above_50": last["rsi"] > 50,
    }
    score = sum(1 if v else -1 for v in checks.values())
    if score >= 3:
        trend = "صاعد"
    elif score <= -3:
        trend = "هابط"
    else:
        trend = "متذبذب / محايد"

    supports, resistances = swing_levels(d)
    bb_pos = (price - last["bb_lower"]) / (last["bb_upper"] - last["bb_lower"])

    return {
        "last_candle": str(d.index[-1]),
        "price": round(price, 4),
        "trend": trend,
        "score": score,
        "checks": {k: bool(v) for k, v in checks.items()},
        "ema20": round(last["ema20"], 4),
        "ema50": round(last["ema50"], 4),
        "ema200": round(last["ema200"], 4),
        "rsi": round(last["rsi"], 1),
        "macd_hist": round(last["macd_hist"], 4),
        "bollinger_position": round(bb_pos, 2),  # 0 = lower band, 1 = upper band
        "atr": round(a, 4),
        "atr_pct": round(a / price * 100, 2),
        "volume_vs_avg20": round(last["vol_ratio"], 2),
        "supports": supports,
        "resistances": resistances,
        # ATR-based reference levels, not signals
        "long_reference": {"stop": round(price - 1.5 * a, 4), "tp1": round(price + 2 * a, 4), "tp2": round(price + 3 * a, 4)},
        "short_reference": {"stop": round(price + 1.5 * a, 4), "tp1": round(price - 2 * a, 4), "tp2": round(price - 3 * a, 4)},
        "candles_used": len(d),
        "warning": "ema200 غير موثوق: عدد الشموع أقل من 200" if len(d) < 200 else None,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("symbol", nargs="?", default="ETHUSDT")
    p.add_argument("--interval", default="4h", help="1m 5m 15m 1h 4h 1d ...")
    p.add_argument("--csv")
    p.add_argument("--limit", type=int, default=500)
    args = p.parse_args()
    df = get_data(args.symbol, args.interval, args.csv, args.limit)
    print(json.dumps(analyze(df), ensure_ascii=False, indent=2))
