# Backtest results on real Binance data (run 2026-11-07)

Data: 6,000 candles per series from Binance spot (4h ≈ 2.7 years, 1h ≈ 8 months),
BTCUSDT, ETHUSDT, SOLUSDT. First 70% = in-sample (IS), last 30% = out-of-sample (OOS).
Defaults: stop 1.5 ATR, target 3 ATR, 1% risk, 0.1% fee per side, 0.05% slippage,
one trade at a time, no leverage. `confluence` trades long and short; the others long only.

| coin | tf | strategy | part | trades | win % | avg R | PF | return % | max DD % | buy & hold % |
|---|---|---|---|---|---|---|---|---|---|---|
| BTC | 4h | confluence | IS | 50 | 32.0 | -0.14 | 0.81 | -7.42 | 10.06 | 31.6 |
| BTC | 4h | confluence | OOS | 22 | 36.4 | -0.01 | 0.98 | -0.44 | 8.26 | -16.13 |
| BTC | 1h | confluence | IS | 41 | 26.8 | -0.44 | 0.42 | -16.65 | 17.3 | 8.1 |
| BTC | 1h | confluence | OOS | 19 | 36.8 | -0.18 | 0.73 | -3.37 | 8.22 | -1.2 |
| ETH | 4h | confluence | IS | 39 | 33.3 | -0.07 | 0.91 | -2.95 | 5.82 | -15.84 |
| ETH | 4h | confluence | OOS | 16 | 37.5 | 0.09 | 1.15 | 1.32 | 7.7 | -27.61 |
| ETH | 1h | confluence | IS | 44 | 38.6 | -0.1 | 0.85 | -4.86 | 12.49 | 17.98 |
| ETH | 1h | confluence | OOS | 22 | 45.5 | 0.11 | 1.18 | 2.26 | 4.25 | -8.43 |
| SOL | 4h | confluence | IS | 30 | 33.3 | -0.06 | 0.91 | -2.09 | 7.13 | -25.48 |
| SOL | 4h | confluence | OOS | 22 | 40.9 | 0.14 | 1.21 | 2.77 | 7.94 | -33.94 |
| SOL | 1h | confluence | IS | 39 | 30.8 | -0.24 | 0.68 | -9.31 | 11.89 | 6.28 |
| SOL | 1h | confluence | OOS | 23 | 39.1 | -0.0 | 1.0 | -0.28 | 5.04 | -3.95 |

The other built-in strategies (trend_pullback, breakout, mean_reversion) were also
negative or break-even overall; breakout looked good on ETH 4h in-sample (PF 1.49)
and then lost in out-of-sample (PF 0.37), a textbook overfit.

A parameter search over 66 combinations (stop 1.5/2/2.5 ATR, target 2/3/4 ATR,
ADX 20/25, long-only vs both sides) found **no setting with a positive average R
in-sample** across the six data sets.

## Conclusion

Standard indicator signals (EMA, RSI, MACD, ADX, Bollinger, breakouts) on these
liquid coins do not show an edge after fees. What the tools reliably do is cap the
loss per trade (fixed 1% risk, max drawdown stayed 4–17% while buy-and-hold swung
−34% to +32%). Present any signal from them as a structured plan with defined risk,
never as an accurate prediction. Re-run this test before quoting newer numbers.

## Fear & Greed index filter (run 2026-11-07)

Daily index from api.alternative.me (since 2018), lagged one day so no candle sees
a value before it was published. 4h candles, BTC/ETH/SOL, same costs as above.
Modes: `contrarian` = confluence longs only in fear (<50), shorts only in greed (>50);
`momentum` = the opposite; `fear_buy` = long on a green candle when index ≤ 20;
`greed_sell` = short on a red candle when index ≥ 80.

| mode | last 1000 candles PF (trades) | 6000 candles IS PF (trades) | OOS PF (trades) |
|---|---|---|---|
| baseline confluence | 1.15 (36) | 0.86 (119) | 1.11 (60) |
| contrarian | 1.08 (10) | 1.19 (24) | 0.68 (17) |
| momentum | 1.19 (26) | 0.84 (98) | 1.33 (43) |
| fear_buy | 1.06 (32) | 1.30 (62) | 0.86 (104) |
| greed_sell | – (0) | 1.06 (51) | – (0) |

Every filter that helped in one period hurt in the other (fear_buy, contrarian,
momentum all flip). 1000 4h candles give only ~10–36 trades across three coins,
too few to tell anything apart. **Conclusion: the Fear & Greed index adds no
reliable edge**; it was not added to the indicator.

## Long-term: buy & hold vs daily trend following vs weekly DCA (run 2026-11-07)

`scripts/longterm.py`, Binance daily closes, 0.1% fee + 0.05% slippage per switch.
Trend = hold the coin while its daily close is above its SMA, otherwise cash. Each
coin is an equal, separate share of the capital (no rebalancing). CAGR / max drawdown:

| basket (period) | buy & hold | trend SMA50 | trend SMA100 | trend SMA200 | DCA $100/week |
|---|---|---|---|---|---|
| BTC (2018-03 → 2026-11) | 24.4% / −76.6% | 43.3% / −58.5% | 40.6% / −38.8% | 25.0% / −64.4% | +361% on $45.3k, worst −52% |
| BTC+ETH (same) | 19.4% / −81.1% | 46.3% / −56.5% | 35.0% / −56.1% | 27.2% / −61.1% | +334% on $45.3k, worst −62% |
| 8 coins* (2021-02 → 2026-11) | 15.1% / −85.3% | 39.4% / −51.2% | 11.4% / −80.8% | 31.5% / −63.6% | +24% on $29.8k, worst −56% |

*BTC ETH BNB SOL XRP ADA DOGE LINK: today's large coins, so the basket has
survivorship bias (coins that died since 2021 are not in it).

BTC year by year, trend SMA100 vs hold: it lost less in down years (2018 −45% vs
−72%, 2022 −21% vs −65%) and gained less in strong up years (2020 +166% vs +302%,
2023 +82% vs +155%, 2024 +57% vs +112%).

Reading: trend following beat holding in 8 of 9 cases and cut the worst drawdown,
mainly by being in cash for most of the 2018 and 2022 bear markets. The result
depends a lot on the SMA length (8 coins: SMA100 lost to holding while SMA50/200
won), drawdowns were still 39–81%, and the sample holds only about two full
crypto cycles. It is the only approach here with a positive result across tests,
not a guarantee.

## Candlestick patterns and RSI divergence (run 2026-11-07)

Same 6 data sets (BTC/ETH/SOL, 4h and 1h, 6000 candles). "Direction edge" = how
much more often price moved the pattern's way over the next 6 candles than it does
on an average candle. Trades: entry next open, 1.5 ATR stop, 3 ATR target, costs.
Divergence: price lower low / higher high between confirmed pivots (5 candles each
side, signal only after confirmation) with RSI higher low < 40 / lower high > 60.

| pattern | signals | direction edge | trades | win % | avg R | PF | profitable sets |
|---|---|---|---|---|---|---|---|
| bullish engulfing | 3227 | −0.9% | 1408 | 31.8 | −0.20 | 0.73 | 0/6 |
| bearish engulfing | 3392 | −2.2% | 1531 | 32.9 | −0.16 | 0.78 | 0/6 |
| hammer | 1736 | +2.0% | 940 | 32.6 | −0.19 | 0.75 | 0/6 |
| shooting star | 1531 | +1.8% | 881 | 29.7 | −0.26 | 0.67 | 0/6 |
| morning star | 372 | −2.3% | 333 | 32.4 | −0.20 | 0.73 | 1/6 |
| evening star | 426 | +0.8% | 369 | 35.2 | −0.10 | 0.86 | 1/6 |
| RSI bullish divergence | 144 | +1.5% | 142 | 26.8 | −0.35 | 0.57 | 0/6 |
| RSI bearish divergence | 150 | +7.4% | 143 | 32.2 | −0.19 | 0.74 | 1/6 |

Direction edges are within noise (about ±1–4% standard error at these counts) and
every pattern lost money as a stand-alone trade. Use them, if at all, as context at
a level the plan already identified, never as a signal on their own.

## Daily, with the trend, 1:3, one compounding $40,000 account (run 2026-11-07)

`scripts/portfolio.py BTCUSDT ETHUSDT SOLUSDT --capital 40000 --risk 1 --stop-atr 1.5
--target-atr 4.5 --entry <entry>`. Long only while EMA50 > EMA200 and close > SMA100;
1% of the current balance risked per trade; max one trade per coin; no leverage;
fee + slippage both ways; gaps through the stop exit at the open. 2018-03 → 2026-11.

| entry | final balance | return | CAGR | max DD | trades | win % | PF | longest losing streak |
|---|---|---|---|---|---|---|---|---|
| pullback (RSI back above 40) | $41,453 | +3.6% | 0.4% | 15.1% | 42 | 28.6 | 1.15 | 11 |
| **breakout (close > 20-day high)** | **$81,835** | **+104.6%** | **8.6%** | **11.9%** | 135 | 40.0 | 1.90 | 10 |
| new trend (close crosses SMA100) | $46,306 | +15.8% | 1.7% | 13.0% | 39 | 35.9 | 1.61 | 8 |

Breakout checks: positive on each coin (BTC +$13.0k, ETH +$14.2k, SOL +$14.6k);
stop/target 1/3, 1.5/4.5, 2/6 ATR gave +72.5%, +104.6%, +104.9%; risking 2% instead
of 1% gave $158,227 (+296%, CAGR 17.2%) with max DD 22.3%. Yearly at 1%: 2018 0,
2019 +7.7, 2020 +23.6, 2021 +27.4, 2022 0, 2023 +15.6, 2024 +8.9, 2025 −1.1,
2026 −3.1 — no trades in the 2018/2022 bear markets, weaker in the last two years.

Same breakout idea on 4h/1h without the daily trend filter lost money (see above):
the daily timeframe plus the trend filter is what changed the outcome. Three entries
were tested and all three had PF > 1; breakout is the best of the three, which adds
some selection bias. Buy & hold of BTC+ETH over the same years returned more
(+365%) but with an 81% drawdown.

### With interest on idle cash (`--cash-yield`)

Same breakout test; uninvested cash earns a fixed annual rate. Final balance from $40,000:

| risk per trade | no interest | 3% on cash | 5% on cash |
|---|---|---|---|
| 1% | $81,835 (CAGR 8.6%, DD 11.9%) | $104,037 (11.6%, 10.5%) | $121,623 (13.7%, 9.5%) |
| 2% | $158,227 (17.2%, 22.3%) | $198,065 (20.2%, 21.2%) | $229,227 (22.3%, 20.5%) |

A deposit alone at 2/3/4/5% for the same 8.68 years: $47,502 / $51,700 / $56,222 / $61,092.
Real rates moved a lot over 2018–2026 (near zero for some years), so a fixed rate is a
simplification.

## Day trading on 1h candles, 1:2, closed the same day (run 2026-11-07)

`scripts/intraday.py`, BTC/ETH/SOL 1h, 2023-06-06 → 2026-11-07 (30,000 candles each),
$40,000 split equally per coin, 1% risk of the coin's current balance, one trade per
coin per day, direction from the daily trend at the previous close, everything closed
by the day's last candle. IS = first 70%, OOS = last 30%.

| setup | sides | final balance | return | max DD | trades | win % | PF | IS PF | OOS PF |
|---|---|---|---|---|---|---|---|---|---|
| opening-range breakout | both | $15,140 | −62.1% | 62.8% | 1444 | 35.6 | 0.60 | 0.65 | 0.52 |
| opening-range breakout | long | $22,436 | −43.9% | 44.8% | 859 | 36.1 | 0.60 | 0.64 | 0.34 |
| volatility breakout | both | $15,870 | −60.3% | 60.4% | 950 | 31.8 | 0.51 | 0.57 | 0.43 |
| volatility breakout | long | $24,351 | −39.1% | 39.2% | 545 | 33.0 | 0.53 | 0.55 | 0.44 |
| 1h RSI pullback | both | $38,793 | −3.0% | 4.0% | 90 | 42.2 | 0.80 | 0.77 | 0.89 |
| 1h RSI pullback | long | $39,271 | −1.8% | 3.7% | 44 | 45.5 | 0.74 | 0.67 | 1.63 (4 trades) |

Costs check (both sides, full period): at 0.02% fee and no slippage ORB ended at
$30,636 and volatility breakout at $25,219; even at zero cost they lost (−14.1%,
−31.9%), so the entries themselves have no edge. The pullback setup turned slightly
positive without costs (+3.0% at 0.02%, +3.9% at zero) on only 90 trades in 3.4 years.

**Conclusion: no tested day-trading setup with 1:2 made money after realistic costs.**
The daily trend filter that rescued the daily breakout strategy did not rescue them.

## Published intraday effects, replicated on Binance 1h 2023-06 → 2026-11 (run 2026-11-07)

1. **Intraday time-series momentum** (Shen, Urquhart & Wang, Financial Review 2022):
   first-hour sign → last hour, and 00–22h sign → last 2 hours. Gross edge 0.6–3.2 bp
   per trade, t-stat −0.4 to 1.6: **not replicated**.
2. **Time of day** (Padysak & Vojtko 2022, Gemini 2015–2022: best hours 21–23 UTC):
   long from the 21:00 open to the 23:00 open every day. Gross per trade: BTC 6.4 bp
   (t 3.4), ETH 10.0 bp (t 3.8), SOL 10.7 bp (t 2.9), positive in 3–4 of 4 years:
   **replicated on independent data**. BTC hourly averages: 21h +2.6 bp, 22h +3.8 bp
   (8h +3.5 bp also high; 23h −2.2 bp).

$40,000 split equally across BTC/ETH/SOL every evening, by round-trip cost:

| cost per round trip | every day: final / CAGR / max DD | daily-uptrend days only |
|---|---|---|
| zero | $118,032 / 37.2% / 13.5% | $59,443 / 12.3% / 9.4% |
| 0.04% (futures maker 0.02% ×2) | $71,612 / 18.6% / 18.5% | $49,656 / 6.5% / 10.8% |
| 0.06% (maker + 1 bp slippage each side) | $55,776 / 10.2% / 21.3% | $45,383 / 3.8% / 11.5% |
| 0.15% (spot maker with BNB) | $18,103 / −20.7% / 54.9% | $30,267 / −7.8% / 30.8% |
| 0.30% (taker + slippage) | $2,769 / −54.2% / 93.1% | $15,397 / −24.4% / 62.4% |

Yearly at 0.04%: 2023 (Jun–Dec) +10.1%, 2024 +50.4%, 2025 +15.9%, 2026 −6.9%.
The edge is real but about 0.06–0.11% per trade, so it only survives with near-zero
costs (futures limit orders; maker fills are not guaranteed and tend to miss the best
days), it weakened in 2025–2026, and the daily trend filter hurt it. Only a paper
trade measuring real fills and fees can tell whether it is usable.

## Day-trading search with a held-out final year (run 2026-11-07)

66 combinations (orb / vbreak / pullback × R:R 1, 1.5, 2, 3 × both/long × trend on/off;
evening window with 0.5/1 ATR stop × R:R, or time-only) were ranked on 2023-06-06 →
2025-11-06 only, then the winner was run unchanged on 2025-11-07 → 2026-11-07.
Costs per side: spot with BNB 0.075% + 0.02% slippage; futures taker with BNB 0.045% +
0.02%; futures maker with BNB 0.018%, no slippage.

- Ranked on futures-taker cost, the best training result was +1.2% over 2.4 years (50
  trades); nothing with ≥100 trades was positive.
- Ranked on futures-maker cost, the winner was the time-only evening trade (long 21:00
  → 23:00 UTC, whole balance, no stop/target), training +61.6%, PF 1.24.

Winner on the unseen last year, $40,000, 1,095 trades:

| cost | final balance | return | max DD | PF |
|---|---|---|---|---|
| none | $48,232 | +20.6% | 8.8% | 1.24 |
| futures maker + BNB | $42,293 | +5.7% | 13.6% | 1.07 |
| futures taker + BNB | $30,006 | −25.0% | 32.2% | 0.75 |
| spot + BNB | $24,098 | −39.8% | 43.5% | 0.60 |

Adding a 1 ATR stop with a 1:1 / 1:1.5 / 1:2 / 1:3 target to the evening trade made
it worse (last year, maker + BNB: −10.3% / −6.8% / −7.0% / −4.5%). The pullback setup
stayed near zero at every R:R (40 trades, −0.2% to +0.5% after taker + BNB).
