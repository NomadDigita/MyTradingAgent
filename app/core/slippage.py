from __future__ import annotations

from statistics import mean

from app.core.models import Candle, SlippageEstimate


class LiquiditySlippageModel:
    """Estimates market-impact bps from recent candle dollar volume and volatility."""

    def estimate(self, symbol: str, candles: list[Candle], notional: float) -> SlippageEstimate:
        if len(candles) < 20 or notional <= 0:
            return SlippageEstimate(symbol, notional, 50.0, 0.0, ["insufficient liquidity history"])
        dollar_volumes = [c.close * c.volume for c in candles[-30:] if c.close > 0 and c.volume > 0]
        average_dollar_volume = mean(dollar_volumes) if dollar_volumes else 0.0
        participation = notional / max(average_dollar_volume, 1e-9)
        ranges = [(c.high - c.low) / c.close for c in candles[-30:] if c.close > 0]
        average_range = mean(ranges) if ranges else 0.0
        estimated_bps = min(250.0, (participation**0.5 * 35.0) + (average_range * 10_000 * 0.08))
        liquidity_score = max(0.0, min(1.0, 1.0 - participation * 4.0 - average_range * 3.0))
        notes = [
            f"avg dollar volume={average_dollar_volume:.2f}",
            f"participation={participation:.5f}",
            f"avg range={average_range:.5f}",
        ]
        return SlippageEstimate(
            symbol=symbol,
            notional=notional,
            estimated_bps=round(estimated_bps, 4),
            liquidity_score=round(liquidity_score, 4),
            notes=notes,
        )
