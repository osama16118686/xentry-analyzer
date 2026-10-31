# Built-in strategies (long-only, spot)

All use: entry at the next candle's open, stop = entry − 1.5 ATR, target = entry + 3 ATR
(R:R ≈ 2 before fees), 1% risk per trade, 0.1% fee per side, 0.05% slippage.
When stop and target are both inside one candle, the backtest assumes the stop hit first.

## trend_pullback
- **Idea:** buy dips inside an uptrend.
- **Condition:** EMA50 > EMA200, RSI was below 40 on the previous candle and closes back at or above 40.
- **Works in:** steady uptrends. **Fails in:** trend reversals and ranges.

## breakout
- **Idea:** ride momentum when price breaks a range.
- **Condition:** close above the previous 20-candle high, volume > 1.5× its 20-candle average, close above EMA200.
- **Works in:** volatility expansion after consolidation. **Fails in:** choppy markets (false breakouts).

## mean_reversion
- **Idea:** buy oversold extremes.
- **Condition:** close below lower Bollinger band, RSI < 30, price no more than 15% under EMA200.
- **Works in:** ranges. **Fails in:** crashes (catching a falling knife). Highest risk of the three.

## Reading results
| Metric | Meaning | Minimum to consider |
|---|---|---|
| trades | sample size | ≥ 30 |
| win_rate_pct | % of winning trades | depends on R:R; with R:R 2, break-even ≈ 34% |
| avg_r | average result in units of risk | > 0.2 |
| profit_factor | gross wins / gross losses | > 1.3 in and out of sample |
| max_drawdown_pct | worst peak-to-trough equity fall | tolerable for the user |
| buy_and_hold_pct | doing nothing but holding | strategy should justify its effort |
