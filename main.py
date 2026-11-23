"""Momentum trend-follower for cbBTC (CBBTC/USDC) on 1-minute bars.

Strategy (long only, one asset, full size, at most a handful of trades):

  * Keep the last 120 closes of CBBTC (2 hours of 1-minute bars).
  * ENTER (buy 100% of cash) when the 120-bar return is at least +0.50%:
    the market has actually moved up over two hours, not just wiggled on
    one minute. A round trip costs about 26 bps in fee, slippage and price
    impact, so a trade needs a real move behind it.
  * EXIT (sell the whole position) when the 120-bar return is at most
    -1.50%: the two-hour trend has genuinely broken down. No trailing stop
    and no take-profit: on the dev window both only added whipsaw exits in
    flat chop (measured: a 1% trailing stop turned +$29.50 into +$1.32).
  * Otherwise hold. Re-entry is allowed when momentum turns positive again.

Why this shape: on the frozen 24h dev window BTC rose +3.6% in one early
rally (hours 2-6) and then chopped sideways. Fast EMA crosses (8/21, 12/26)
traded 70-100 times and lost $115-120 to fees and whipsaw; slow EMA crosses
lost $21-35. This momentum rule traded once on the dev window, rode the
rally and held through the chop: net PnL +$31.09 after all fees, 1 trade,
max drawdown 1.97%. On the time-reversed window (a steady -3.6% fall) the
same rule lost $27.77 versus $38.39 for buy-and-hold, because the -1.50%
exit cuts the position instead of riding the fall to the end.

All math is integer math on the harness's scaled prices (price_scale 5), so
two runs on the same bars produce the same orders byte for byte. No clock,
no environment, no randomness, no network, standard library only.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
LOOKBACK_BARS = 120          # 2 hours of 1-minute bars
ENTRY_BPS = 50               # buy when 120-bar return >= +0.50%
EXIT_BPS = -150              # sell when 120-bar return <= -1.50%
MAX_SLIPPAGE_BPS = 100       # 1% past the latest close; fills move ~13 bps

# The closes seen so far, oldest first. Appended only on batches that carry
# a CBBTC bar (a minute with no sample has no bar and adds nothing).
closes = []


def _return_bps(now, then):
    """(now - then) / then in basis points, integer math, truncating."""
    return (now - then) * 10000 // then


def on_batch(state, batch):
    if state.warming_up:
        return []
    bar = None
    for b in batch["bars"]:
        if b["symbol"] == SYMBOL:
            bar = b
            break
    if bar is None:
        return []
    close = int(bar["c"])
    if close <= 0:
        # Prices are positive integers; a zero or negative close is bad
        # data, not a market move. Skipping the bar keeps it out of the
        # lookback -- a zero there would crash _return_bps with a
        # ZeroDivisionError 121 bars later -- and avoids trading on it.
        return []
    closes.append(close)
    if len(closes) <= LOOKBACK_BARS:
        return []
    ret = _return_bps(close, closes[-LOOKBACK_BARS - 1])
    held = state.positions.get(SYMBOL)
    if held is not None and held.qty > 0:
        if ret <= EXIT_BPS:
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []
    if ret >= ENTRY_BPS:
        cash = state.cash
        min_notional = int(state.hello["fees"]["min_notional_quote_units"])
        if cash >= min_notional:
            return [{"side": "buy", "symbol": SYMBOL,
                     "notional_quote_units": cash,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
