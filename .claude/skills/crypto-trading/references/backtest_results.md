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
