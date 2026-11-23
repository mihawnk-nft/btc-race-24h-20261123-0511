# BTC Race Bot — Momentum Trend-Follower for cbBTC

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/mihawnk-nft/btc-race-24h-20261123-0511/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/mihawnk-nft/btc-race-24h-20261123-0511/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A bot for [Race a BTC trading bot live for 24 hours](https://make.fun/c/btc-race-24h-20261123-0511)
on make.fun. It trades Coinbase Wrapped BTC (cbBTC/USDC) on 1-minute bars from
the Orca Whirlpool on Solana, long only, starting from $1,000 of paper money.
Python 3.13, pure standard library — nothing is installed before the run.

## Strategy

Momentum trend-following with a long lookback, built to trade rarely:

- Keep the last 120 closes of CBBTC (2 hours of 1-minute bars).
- **Enter** — buy 100% of cash when the 120-bar return is at least **+0.50%**:
  the market has actually moved up over two hours, not just wiggled on one
  minute. A full round trip costs about 26 bps in fee, slippage and price
  impact, so a trade needs a real move behind it.
- **Exit** — sell the whole position when the 120-bar return is at most
  **−1.50%**: the two-hour trend has genuinely broken down.
- Otherwise hold. Re-entry is allowed when momentum turns positive again.

No trailing stop and no take-profit: both were measured on the dev window
and only added whipsaw exits in flat chop (a 1% trailing stop turned
+$29.50 into +$1.32). All math is integer math on the harness's scaled
prices, so two runs on the same bars produce identical orders.

## Why this shape

On the frozen 24h dev window BTC rose +3.6% in one early rally (hours 2–6)
and then chopped sideways. Measured locally on that window:

| Strategy | Net PnL | Trades | Max DD |
| --- | --- | --- | --- |
| EMA cross 8/21 | −$114.83 | 76 | 11.64% |
| EMA cross 12/26 | −$119.82 | 70 | 12.02% |
| EMA cross 30/90 | −$21.01 | 9 | 2.60% |
| Buy-and-hold | +$32.17 | 1 | 1.97% |
| **This bot (momentum 120, +0.50% / −1.50%)** | **+$31.09** | **1** | **1.97%** |

Fast EMA crosses churned 70–100 times and bled fees plus whipsaw losses.
This rule traded once, rode the rally and held through the chop. On the
time-reversed window (a steady −3.6% fall) the same rule lost $27.77 versus
$38.39 for buy-and-hold, because the −1.50% exit cuts the position instead
of riding the fall to the end.

## Verification

- Run end-to-end against the kit's own harness engine (`sim/bars/engine.ts`)
  on the frozen dev window, twice: **net PnL +$31.094973, 1 fill, max
  drawdown 1.97%, `aborted: null`, `no_future_bars: true`**, identical
  result on both runs. Dev gate (PnL > $0) and guardrails (≥1 trade,
  drawdown ≤ 25%) both pass.
- `grade-local --driver process` cannot grade a Python bot (it runs Node
  only, and this VM has no Docker), so the harness-engine run above is the
  local grade; it uses the kit's exact fill math, not a reimplementation.

## Layout

- `main.py` — the bot (entrypoint, Python 3.13, stdlib only).
- `vendor/makefun_bars.py` — byte-identical copy of the kit's Python SDK
  shim (`sdk/makefun_bars.py`), kept under `vendor/` as the kit allows.
- `LICENSE` — MIT.

## Simulation only

Every bot trades paper money against real on-chain prices. No real money
is traded.
