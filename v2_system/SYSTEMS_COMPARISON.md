# Candidate systems: one-page comparison for the Nov 28 review

Saved Nov 17, 2026. All figures are backtests from Mar 2022 to Nov 2026, on $46k, at × 1 risk (A $400 / B $200, other strategies $200).

The "hidden" column is the hidden test: 2025 to Nov 2026, data not used in design.

The "realistic 1y" column is a compounding Monte Carlo. It uses 3-month blocks of real months and cuts the edge by 30%.

| System | What it is | %/yr | Max DD | Return/DD | Hidden test %/yr (DD) | Realistic 1y median | P(losing year) | Trades/week | Status |
|---|---|---|---|---|---|---|---|---|---|
| **V1 (live)** | ML 4h on BTC/ETH (+SOL), 1:1, EMA200 | 17.4 | 24.3 | 0.72 | about 20 | n/a | n/a | 3.8 | LIVE (STRATEGY.md) |
| C6 | ML POWER+OI + daily breakout + 4h range | 22.5 | 9.3 | 2.41 | 19.2 (5.9) | n/a | n/a | 3.8 | research |
| **V2.0** | C6 + smart S/R target + XRP ML + levels fade (crowd contra) | 35.9 | 10.9 | 3.30 | 34.3 (7.5) | +26% | about 6% | 6.7 | research, PAPER-TRACKED since Nov 17 |
| V2.1 | V2.0 + squeeze breakout (3-ATR trail) | 50.5 | 13.7 | 3.68 | 58.9 (10.1) | +37% | about 7% | 8.3 | candidate, paper-tracked (tag v21) |
| **V2.2** | V2.1 + daily ML + gold breakout + total open-risk cap $2,400 | 56.5 | 13.1 | 4.30 | 64.1 (10.6) | +43% | about 5% | 9.1 | candidate (not yet paper-tracked) |

## Risk scaling (V2.0 / V2.1). Realistic 1y median and P(DD > 20%)

| Scale | V2.0 | V2.1 |
|---|---|---|
| × 1.0 | +26%, 0% | +36%, 2% |
| × 1.2 | +32%, 0.4% | +45%, 5% |
| × 1.4 | +37%, 1.3% | +53%, 11% |
| × 2.0 | +56%, 9% | +77%, 31% |

## How we pick the system to use (decision rules for Nov 28)

1. **Profit vs drawdown.** Return/DD (higher is better) decides first. Then max DD must be within what the user can hold. The suggested limit is DD ≤ 15% at the chosen risk.
2. **Hidden test.** The candidate must hold up in 2025–26 (the hidden column), not only in the design years.
3. **Paper results.** V2 paper tracking from Nov 17 to Nov 28 must not contradict the backtest. Too few trades is "no contradiction", not "proof".
4. **Live V1 results.** The live phase-1 results tell us whether the user's execution matches the backtest. That matters for any system.
5. **Workload.** 9 trades a week (V2.2) needs a solid routine. If that is too much, take a simpler system.
6. **Phase in.** Don't jump straight to V2.2. Add one component at a time and keep V1 as the fallback:
   1. smart target + OI filter
   2. levels fade
   3. XRP
   4. breakout and range
   5. squeeze
   6. daily ML
   7. gold

## Caveats

- More than 300 variants were tested in total, so expect live results below the backtest. The realistic column already cuts the edge by 30%.
- V2.2 relies heavily on two fat-tailed parts: squeeze (about 15%/yr) and the ML engine (about 23%/yr).
- Live crowd and OI data come from OKX, which only approximates the Binance archive used in the backtest.

## V2.2 compounding (realistic: edge −30%, block bootstrap). Median (bad case p5) on $46k / $80k, and P(DD > 20%)

| Scale | 1 year | 2 years | 3 years |
|---|---|---|---|
| × 1.0 | 46k → 65k (46k) / 80k → 114k; DD20 1% | 46k → 94k (55k) / 80k → 163k; DD20 5% | 46k → 136k (72k) / 80k → 237k; DD20 8% |
| × 1.2 | 46k → 69k (46k) / 80k → 120k; DD20 4% | 46k → 107k (57k) / 80k → 186k; DD20 12% | 46k → 165k (77k) / 80k → 287k; DD20 19% |
| × 1.4 | 46k → 74k (45k) / 80k → 128k; DD20 9% | 46k → 122k (59k) / 80k → 212k; DD20 22% | 46k → 200k (82k) / 80k → 348k; DD20 34% |
| × 2.0 | 46k → 88k (44k) / 80k → 153k; DD20 29% | 46k → 172k (63k) / 80k → 298k; DD20 55% | 46k → 337k (97k) / 80k → 586k; DD20 71% |
