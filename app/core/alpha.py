from __future__ import annotations

from app.core.data_quality import DataQualityGate
from app.core.indicators import atr, ema, rsi, sma
from app.core.models import AlphaCard, AlphaVote, Candle, SignalAction


class AlphaConfluenceEngine:
    """Original confluence engine combining several transparent alpha voters."""

    def __init__(self) -> None:
        self.quality_gate = DataQualityGate()

    def card(self, symbol: str, candles: list[Candle]) -> AlphaCard:
        quality = self.quality_gate.evaluate(symbol, candles)
        if len(candles) < 60 or not quality.valid:
            return AlphaCard(symbol, 0.0, SignalAction.FLAT, 0.0, [], quality)

        closes = [c.close for c in candles]
        volumes = [c.volume for c in candles]
        fast = ema(closes, 12)
        slow = ema(closes, 26)
        rsi_values = rsi(closes, 14)
        atr_values = atr(candles, 14)
        volume_average = sma(volumes, 20)
        last = candles[-1]
        vwap = _rolling_vwap(candles[-48:])

        votes = [
            self._trend_vote(fast[-1], slow[-1], closes[-1]),
            self._momentum_vote(rsi_values[-1] if rsi_values else 50.0),
            self._vwap_vote(last.close, vwap),
            self._volatility_vote(atr_values[-1] / closes[-1] if atr_values and closes[-1] else 0.0),
            self._volume_vote(volumes[-1], volume_average[-1] if volume_average else volumes[-1]),
        ]
        weighted = sum(v.direction * v.confidence for v in votes)
        confidence = min(1.0, sum(v.confidence for v in votes) / len(votes))
        score = round(weighted / max(len(votes), 1), 4)
        if score > 0.18 and confidence >= 0.45:
            action = SignalAction.LONG
        elif score < -0.18 and confidence >= 0.45:
            action = SignalAction.SHORT
        else:
            action = SignalAction.FLAT
        return AlphaCard(symbol, score, action, round(confidence, 4), votes, quality)

    def _trend_vote(self, fast: float, slow: float, price: float) -> AlphaVote:
        spread = (fast - slow) / max(price, 1e-9)
        direction = 1.0 if spread > 0 else -1.0
        confidence = min(1.0, abs(spread) * 80)
        return AlphaVote("ema_trend", direction, confidence, f"EMA spread {spread:.5f}")

    def _momentum_vote(self, value: float) -> AlphaVote:
        if value >= 60:
            return AlphaVote("rsi_momentum", 0.7, min(1.0, (value - 50) / 30), f"RSI {value:.2f}")
        if value <= 40:
            return AlphaVote("rsi_momentum", -0.7, min(1.0, (50 - value) / 30), f"RSI {value:.2f}")
        return AlphaVote("rsi_momentum", 0.0, 0.25, f"RSI neutral {value:.2f}")

    def _vwap_vote(self, price: float, vwap: float) -> AlphaVote:
        distance = (price - vwap) / max(vwap, 1e-9)
        if abs(distance) < 0.002:
            return AlphaVote("rolling_vwap", 0.0, 0.2, f"price near VWAP {distance:.4f}")
        direction = 0.5 if distance > 0 else -0.5
        return AlphaVote("rolling_vwap", direction, min(0.8, abs(distance) * 35), f"VWAP distance {distance:.4f}")

    def _volatility_vote(self, atr_pct: float) -> AlphaVote:
        if atr_pct > 0.06:
            return AlphaVote("atr_risk", 0.0, 0.95, f"ATR risk high {atr_pct:.4f}")
        if atr_pct < 0.008:
            return AlphaVote("atr_risk", 0.0, 0.25, f"ATR low {atr_pct:.4f}")
        return AlphaVote("atr_risk", 0.15, 0.45, f"ATR acceptable {atr_pct:.4f}")

    def _volume_vote(self, volume: float, average: float) -> AlphaVote:
        ratio = volume / max(average, 1e-9)
        if ratio >= 1.4:
            return AlphaVote("participation", 0.25, min(1.0, ratio / 2), f"volume ratio {ratio:.2f}")
        if ratio <= 0.45:
            return AlphaVote("participation", -0.15, 0.4, f"thin participation {ratio:.2f}")
        return AlphaVote("participation", 0.0, 0.25, f"volume ratio {ratio:.2f}")


def _rolling_vwap(candles: list[Candle]) -> float:
    numerator = sum(((c.high + c.low + c.close) / 3) * c.volume for c in candles)
    denominator = sum(c.volume for c in candles)
    if denominator <= 0:
        return candles[-1].close if candles else 0.0
    return numerator / denominator
