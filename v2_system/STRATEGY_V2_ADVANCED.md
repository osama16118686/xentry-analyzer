# STRATEGY V2: advanced version (saved Nov 17, 2026). NOT LIVE.

The live system is still `STRATEGY.md` (V1), and V1 stays unchanged.

V2 is a separate, complete rule set. It goes live only if the user approves it, for example at the Nov 28 review. V1 stays saved so we can always go back.

Research scripts: fund_all.py (merged test), fund_engine.py, fund_multi.py, fund_levels.py, fund_adaptive.py, fund_coins.py.

---
## Market and sizing
- Binance USDT-M perpetual futures, long and short, 4h base timeframe.
- Coins:
  - BTCUSDT, ETHUSDT and SOLUSDT: all 4 strategies.
  - XRPUSDT: strategy 1 (ML) only.
- Risk per trade at phase 1 ($46k):
  - B = $200
  - A = $400
  - A+ = $600
  - Breakout, range and levels trades = $200 each
- Risk scaling plan (needs user approval each step): × 1.0 first, then × 1.2, then × 1.4. At × 1.4 the backtest gives about 50%/yr with DD about 15%.

## Strategy 1: ML engine (main profit source, about 23%/yr in backtest)
Signal:
- BTC and ETH: `ml_signals.py signal BTCUSDT ETHUSDT --threshold 0.6`
- SOL: `ml_signals.py signal BTCUSDT ETHUSDT SOLUSDT --trade SOLUSDT --threshold 0.6`
- XRP: `ml_signals.py signal BTCUSDT ETHUSDT XRPUSDT --trade XRPUSDT --threshold 0.6` (the hybrid model trained on BTC+ETH+XRP)

All of these must hold:
1. p ≥ 0.60 on the last closed 4h candle.
2. EMA200 (4h) filter: long only if price > EMA200, short only if price < EMA200.
3. POC filter: volume profile of the last 120 1h candles (50 bins). Long only if price > POC, short only if price < POC. Not applied on XRP, which was tested without it.
4. ADX(14, 4h) ≥ 20.
5. Open interest now < open interest 24h ago. Live source: OKX through live_futures.py.

Grade and risk:
- p < 0.65 → B ($200)
- 0.65 ≤ p < 0.72 → A ($400)
- p ≥ 0.72 → A+ ($600)
- After 3 losing trades in a row, use half risk until the next win.

Orders:
- ATR = ATR(14, 4h); P = the signal close.
- LIMIT entry = P − side × 0.25 × ATR, valid for 2 candles (8h).
- Stop = P − side × 1.5 × ATR.
- **Target (smart target, new in V2):**
  - Find the swing points on 4h. A swing high/low is the extreme of 5 candles on each side, and it only counts once it is confirmed, 5 candles later.
  - Look back over the last 180 candles (30 days).
  - For a long, take the nearest swing high above P + 0.3 ATR. For a short, take the nearest swing low below P − 0.3 ATR.
  - Target distance = 0.9 × (distance from P to that level), clipped to between 0.75× and 1.5× the stop distance (1.5 ATR). If there is no level, use 1.5×.
  - No partial close and no trailing stop.
- Time stop: 30 candles, or 60 if the target ratio is ≥ 1.75.
- Limits: max 4 ML trades open, ML open risk ≤ $1,600.

## Strategy 2: Daily breakout (about 4%/yr)
- Daily candles, ATR(20) daily.
- Long: close > the highest high of the prior 20 days AND close > daily EMA100.
- Short: close < the lowest low of the prior 20 days AND close < daily EMA100.
- Enter at the next daily open. Stop = entry ∓ 2 × daily ATR.
- Exit: a close below the prior 10-day low (long) or above the prior 10-day high (short), at the next open. Or the stop.
- $200 risk. One position per coin. BTC, ETH and SOL only.

## Strategy 3: 4h range mean-reversion (about 2.7%/yr)
- Range = the highest high and lowest low of the prior 30 candles. W = width.
- Active only if ADX(14) < 20 AND W < 8 × ATR.
- Long: the low touches the bottom 10% of the range and the candle closes green, above the range low.
  - Stop = range low − 1 ATR. Target = the middle of the range.
- Short: the mirror at the top 10%, with a red close.
- Time stop: 30 candles. $200 risk. One position per coin. BTC, ETH and SOL only.

## Strategy 4: Strong-level fade with crowd contrarian (the user's idea, about 5.8%/yr)
- Strong level: 3 or more 4h swing points (5 candles each side, confirmed) within 0.5 ATR of each other, in the last 360 candles (60 days).
- Short at resistance. All of these must hold:
  - the candle high reaches the level − 0.2 ATR,
  - the close is below the level,
  - the previous close is below the level,
  - the candle is red,
  - AND the crowd is leaning LONG: the Binance global long/short account ratio z-score (180-candle) is > 0.
- Long at support: the mirror, and the crowd is leaning SHORT (z < 0).
- Enter at the next open. Stop = level ± 1 ATR. Target = 4% from entry (5–6% tested slightly higher but with more DD).
- Time stop: 30 candles. $200 risk. BTC, ETH and SOL only.
- Live crowd data: OKX long/short ratio vs its own recent average (live_futures.py). This is an approximation of the Binance ratio.

## Portfolio rules
- Strategies run side by side, with one position per coin per strategy.
- **Open-risk cap: still TO BE DEFINED before going live.** The theoretical maximum is $3,400 (7.4%). Suggestion: cap total open risk at $2,400 (about 5%) and skip new signals beyond it.
- The 15-minute watcher alerts are info only.

## Backtest, Mar 2022 to Nov 2026, on $46k at × 1.0 risk
- Return: 35.9%/yr. Max DD 10.9%. R/DD 3.30. PF 1.48. Win rate 56%.
- Worst month −7.4%. 26% of months were negative.
- Every year positive: 2022 +39%, 2023 +35%, 2024 +31%, 2025 +29%, 2026 +35%.
- Hidden test 2025–2026: 34.3%/yr, DD 7.5%.
- Trades: about 6.7/week (ML 2.2, levels 2.2, range 1.8, breakout 0.5).
- Stress: double costs → 28.1%/yr, DD 13.4%. Monte Carlo DD 95th percentile 12.8%, 99th percentile 15.5%.
- Realistic one-year view (edge −30%): median +$11.4k (+25%), 5th percentile +$1.8k, P(loss) 2.5%.

## Caveats
- Many variants were tested, so some overfitting is likely. Expect less live.
- Paper-trade or phase in before using full size.
- Phase in one component at a time. Suggested order:
  1. ML smart target
  2. S4 levels
  3. XRP
  4. Breakout and range

---
## RESEARCH RULE (user instruction, Nov 17)
- Every new idea is tested ON TOP OF THE LATEST V2: all accepted ideas included, never on the old system alone, because ideas interact (one can break or duplicate another).
- The baseline for every new test is `build()` in fund_all.py. A new test = baseline + the new idea, compared with the baseline alone (return, DD, R/DD, OOS, years).
- Accept the idea only if it improves R/DD and OOS without a big DD increase, and it holds on neighbouring variants (robustness).
- If accepted:
  - add it to V2,
  - bump the version (V2.1, V2.2, ...),
  - update build() and the changelog below.
- V1 (STRATEGY.md, live) is never changed by research. Moving pieces of V2 into live needs explicit user approval.

## Changelog
- **V2.0 (Nov 17):** ML POWER+OI + smart S/R target + XRP (ML only) + daily breakout + 4h range + strong-level fade with crowd contra (4%).
  - Baseline result: 35.9%/yr, DD 10.9%, R/DD 3.30, OOS 34.3%.
- **Rejected (tested):**
  - liquidation flush bounce
  - funding extremes
  - BTC/ETH and SOL/BTC pairs
  - BNB
  - XRP breakout, range and levels
  - fixed 1:2.5 and 1:3 targets
  - target by model probability or by ADX
  - (Nov 17) momentum rotation, re-entry after stop, structure-break exit (neutral)
- **Candidates pending user approval (Nov 17), each tested on top of V2.0:**
  - squeeze breakout trail 3 ATR: +14.6%/yr, DD +2.8
  - daily-timeframe ML: +4.3%/yr, DD +0.5
  - gold (PAXG) daily breakout: +1.7%/yr, DD +0.2
  - total open-risk cap $2,400: no cost in history
- Rejected Nov 17: same-direction caps, weekend/night time filters, gold range, gold squeeze.
