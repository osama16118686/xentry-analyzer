---
name: crypto-trading
description: Professional crypto day-trading workflow - technical analysis of a coin (BTC, ETH, SOL...), trade plans with entry/stop/targets, position sizing, and backtesting strategies before risking money. Use when the user asks to analyze a coin, wants a trade plan, asks "should I buy/sell", sends a chart screenshot, asks about position size or risk, or wants to test a strategy. Triggers include Arabic requests such as "حلل", "تحليل", "صفقة", "دخول", "وقف خسارة", "الإيثريوم", "البيتكوين", "باك تست".
---

# Crypto Trading

A disciplined workflow for analyzing crypto and planning trades. Its edge is
**process and risk control**, not prediction. No analysis guarantees profit; the goal
is to take only trades with a defined risk, a positive risk/reward, and a strategy
that has been tested on history.

Reply in the user's language (usually Arabic). Keep numbers exact and dated.

## Tools

Scripts are in `scripts/` (run from that directory; needs `pandas`, `numpy`, `requests`).

| Script | Purpose |
|---|---|
| `analyze.py SYMBOL --interval 4h` | Trend, EMA20/50/200, RSI, MACD, Bollinger, ATR, volume, supports/resistances, ATR reference levels |
| `risk.py --capital C --risk 1 --entry E --stop S --target T` | Position size, R:R, break-even win rate, leverage warnings |
| `backtest.py SYMBOL --interval 4h --strategy all --split 0.7 --limit 5000` | Backtest built-in strategies (long and short) with fees and slippage, in-sample vs out-of-sample |
| `longterm.py BTCUSDT ETHUSDT --sma 50 100 200 --dca 100 --yearly 100` | Daily buy & hold vs trend following (close above SMA) vs weekly DCA, with CAGR and max drawdown |
| `chart.py SYMBOL --interval 4h --bars 360 --out chart.png` | Candlestick chart with EMA50/200, support/resistance zones and past strategy signals marked won/lost (needs matplotlib) |
| `tradingview/xentry_signals.pine` | TradingView strategy script: buy/sell signals, stop and target lines, risk-based size, alerts, indicator panel. Same logic as `backtest.py --strategy confluence` |

All scripts accept `--csv file.csv` (columns: time, open, high, low, close, volume)
when the Binance API is unreachable.

**If no market data is reachable** (network blocked, no CSV): use WebSearch for the
current price and published levels from several sources, say clearly that the data
is not live, and ask the user for a chart screenshot or a CSV export.

## Workflow: analyzing a coin

1. **Multi-timeframe data.** Run `analyze.py` on `1d` (main trend), `4h` (structure)
   and `1h` (entry timing). Never trade against the `1d` trend without saying so.
2. **Read the market:**
   - Trend: price vs EMA50/EMA200, and EMA50 vs EMA200
   - Momentum: RSI (>70 stretched, <30 oversold; in a strong trend these can persist), MACD histogram
   - Volatility: ATR % (sets stop distance), Bollinger position
   - Volume: `volume_vs_avg20` > 1.5 confirms breakouts; low volume breakouts often fail
   - Key levels: supports/resistances from the script, plus round numbers
3. **Context check** (WebSearch when possible): major news, BTC direction (alts follow
   BTC), upcoming macro events (CPI, FOMC), unusual funding rates.
4. **Scenarios.** Give bullish, bearish and range scenarios, each with the price level
   that confirms it and the level that invalidates it.
5. **Trade plan** only if the checklist below passes. Otherwise say "no trade" and
   what the user should wait for. "No trade" is a valid, professional answer.

## Trade checklist (all must pass)

- [ ] Stop-loss is defined **before** entry, at a level where the idea is wrong
      (beyond a support/resistance or ≥1 ATR away), not at an arbitrary %
- [ ] Risk/reward ≥ 2 after fees (check with `risk.py`)
- [ ] Risk per trade ≤ 1–2% of capital
- [ ] Entry agrees with the higher-timeframe trend, or is explicitly marked counter-trend with reduced size
- [ ] Not chasing: entry is near a level, not after a large candle far from it
- [ ] The setup type has a positive out-of-sample backtest, or is labeled untested

## Risk rules to always state

- Spot or low leverage only (≤3x); explain that leverage means liquidation risk
- Daily loss limit: stop trading for the day after −3% of capital or 3 losses in a row
- No averaging down on a losing trade
- Avoid low-cap / low-liquidity coins and Telegram/Twitter "signals"

## Backtesting a strategy

Before endorsing any strategy (built-in or the user's own):
1. Run `backtest.py ... --split 0.7` on at least 1000 candles.
2. Require: ≥30 trades, profit factor > 1.3 **in both** in-sample and out-of-sample,
   max drawdown the user can tolerate, and compare to buy-and-hold.
3. If out-of-sample is much worse than in-sample, the strategy is overfitted; say so.
4. Tuning parameters (`--stop-atr`, `--target-atr`) until it looks good on the same
   data is overfitting. Tune on in-sample, judge on out-of-sample only.
5. To test a user's own strategy, add a branch in `signals()` in `backtest.py`.

See `references/strategies.md` for the built-in setups and `references/backtest_results.md`
for measured results on real data. Those results show no strategy here has a proven
edge; never describe a signal from these tools as accurate.

## TradingView indicator

When the user wants signals on their TradingView chart, give them
`tradingview/xentry_signals.pine` and these steps: TradingView → Pine Editor → paste →
Save → Add to chart. Strategy Tester shows its trades and stats on any coin and
timeframe; alerts: Create alert → condition "Xentry Signals" → "alert() function calls only".
Tell them to check its Strategy Tester results on their coin before trusting it.

## Output format (analysis)

```
## تحليل {COIN} — {date/time, data source}
السعر: …  | الاتجاه (يومي / 4 ساعات / ساعة): … / … / …
### المؤشرات
RSI … | MACD … | ATR …% | الحجم …
### المستويات
مقاومة: … ، … ، …
دعم: … ، … ، …
### السيناريوهات
🟢 صعود: يتأكد فوق … ← أهداف … / يُلغى تحت …
🔴 هبوط: يتأكد تحت … ← أهداف … / يُلغى فوق …
⚪ تذبذب: بين … و …
### خطة الصفقة (أو: لا توجد صفقة الآن — انتظر …)
دخول … | وقف … | هدف 1 … | هدف 2 … | R:R … | حجم الصفقة لرأس مال … بمخاطرة 1%: …
⚠️ تحليل تعليمي وليس توصية مالية.
```

## Honesty rules

- Never promise profits or give win-probability numbers that were not measured.
- Always state the data time and source; flag stale data.
- If data is missing or conflicting, say so instead of filling gaps.
