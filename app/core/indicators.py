from __future__ import annotations

from app.core.models import Candle


def ema(values: list[float], period: int) -> list[float]:
    if not values or period <= 0:
        return []
    alpha = 2 / (period + 1)
    result = [values[0]]
    for value in values[1:]:
        result.append((value * alpha) + (result[-1] * (1 - alpha)))
    return result


def sma(values: list[float], period: int) -> list[float]:
    if period <= 0 or len(values) < period:
        return []
    return [sum(values[i - period : i]) / period for i in range(period, len(values) + 1)]


def rsi(values: list[float], period: int = 14) -> list[float]:
    if len(values) <= period:
        return []
    gains: list[float] = []
    losses: list[float] = []
    for previous, current in zip(values, values[1:], strict=False):
        change = current - previous
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    output: list[float] = []
    for i in range(period, len(gains)):
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
        if avg_loss == 0:
            output.append(100.0)
        else:
            rs = avg_gain / avg_loss
            output.append(100 - (100 / (1 + rs)))
    return output


def atr(candles: list[Candle], period: int = 14) -> list[float]:
    if len(candles) <= period:
        return []
    true_ranges: list[float] = []
    previous_close = candles[0].close
    for candle in candles[1:]:
        true_ranges.append(
            max(
                candle.high - candle.low,
                abs(candle.high - previous_close),
                abs(candle.low - previous_close),
            )
        )
        previous_close = candle.close
    if len(true_ranges) < period:
        return []
    output = [sum(true_ranges[:period]) / period]
    for value in true_ranges[period:]:
        output.append(((output[-1] * (period - 1)) + value) / period)
    return output
