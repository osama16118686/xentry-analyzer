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
