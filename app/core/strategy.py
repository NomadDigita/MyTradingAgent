from __future__ import annotations

from app.core.indicators import atr, ema, rsi
from app.core.models import Candle, MarketType, Signal, SignalAction


class MultiFactorStrategy:
    """Conservative baseline strategy.

    This is intentionally simple and inspectable. Treat it as a replaceable
    research module, not a claim of profitability.
    """

    def analyze(self, symbol: str, candles: list[Candle], market_type: MarketType) -> Signal:
        if len(candles) < 60:
            last = candles[-1].close if candles else 0.0
            return Signal(
                symbol,
                SignalAction.FLAT,
                0.0,
                ["Not enough candles"],
                None,
                None,
                last,
                market_type,
            )

        closes = [c.close for c in candles]
        ema_fast = ema(closes, 12)
        ema_slow = ema(closes, 26)
        rsi_values = rsi(closes, 14)
        atr_values = atr(candles, 14)
        last_price = closes[-1]
        last_atr = atr_values[-1] if atr_values else last_price * 0.01
        trend_up = ema_fast[-1] > ema_slow[-1] and ema_fast[-2] <= ema_slow[-2]
        trend_down = ema_fast[-1] < ema_slow[-1] and ema_fast[-2] >= ema_slow[-2]
        momentum = rsi_values[-1] if rsi_values else 50.0

        rationale: list[str] = [
            f"EMA12={ema_fast[-1]:.4f}, EMA26={ema_slow[-1]:.4f}",
            f"RSI14={momentum:.2f}",
            f"ATR14={last_atr:.4f}",
        ]
        confidence = 0.0
        action = SignalAction.FLAT

        if trend_up and 45 <= momentum <= 70:
            action = SignalAction.LONG
            confidence = min(0.85, 0.55 + abs(ema_fast[-1] - ema_slow[-1]) / max(last_price, 1e-9))
            rationale.append("Bullish EMA crossover with acceptable momentum")
            stop_loss = last_price - (2 * last_atr)
            take_profit = last_price + (3 * last_atr)
        elif trend_down and 30 <= momentum <= 55:
            action = SignalAction.SHORT
            confidence = min(0.85, 0.55 + abs(ema_fast[-1] - ema_slow[-1]) / max(last_price, 1e-9))
            rationale.append("Bearish EMA crossover with acceptable momentum")
            stop_loss = last_price + (2 * last_atr)
            take_profit = last_price - (3 * last_atr)
        else:
            stop_loss = None
            take_profit = None
            rationale.append("No actionable alignment")

        return Signal(
            symbol=symbol,
            action=action,
            confidence=round(confidence, 4),
            rationale=rationale,
            stop_loss=stop_loss,
            take_profit=take_profit,
            last_price=last_price,
            market_type=market_type,
        )
