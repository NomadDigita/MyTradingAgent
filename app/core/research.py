from __future__ import annotations

from statistics import mean, pstdev

from app.core.indicators import atr, ema, rsi
from app.core.models import Candle, MarketType, Regime, ResearchReport, SignalAction
from app.core.strategy import MultiFactorStrategy


class InstitutionalResearchEngine:
    """Transparent research layer that scores trend, momentum, volatility, and risk."""

    def __init__(self) -> None:
        self.strategy = MultiFactorStrategy()

    def report(self, symbol: str, candles: list[Candle], market_type: MarketType) -> ResearchReport:
        signal = self.strategy.analyze(symbol, candles, market_type)
        if len(candles) < 60:
            return ResearchReport(
                symbol=symbol,
                action=SignalAction.FLAT,
                confidence=0.0,
                regime=Regime.UNKNOWN,
                volatility=0.0,
                score=0.0,
                last_price=signal.last_price,
                risk_notes=["Insufficient candle history"],
                rationale=signal.rationale,
            )

        closes = [c.close for c in candles]
        returns = [
            (current - previous) / previous
            for previous, current in zip(closes, closes[1:], strict=False)
            if previous
        ]
        volatility = pstdev(returns[-30:]) if len(returns) >= 30 else 0.0
        fast = ema(closes, 20)
        slow = ema(closes, 50)
        rsi_values = rsi(closes, 14)
        atr_values = atr(candles, 14)
        regime = self._regime(fast[-1], slow[-1], rsi_values[-1], volatility)

        trend_score = min(abs(fast[-1] - slow[-1]) / max(closes[-1], 1e-9) * 100, 1.0)
        momentum_score = 1.0 - abs((rsi_values[-1] if rsi_values else 50.0) - 55.0) / 55.0
        volatility_penalty = min(volatility * 15, 0.5)
        score = max(0.0, min(1.0, (trend_score * 0.45) + (momentum_score * 0.35) + 0.2 - volatility_penalty))

        risk_notes: list[str] = []
        if volatility > 0.03:
            risk_notes.append("Elevated realized volatility")
        if atr_values and atr_values[-1] / closes[-1] > 0.05:
            risk_notes.append("Wide ATR relative to price")
        if not risk_notes:
            risk_notes.append("No major quantitative risk note from baseline checks")

        return ResearchReport(
            symbol=symbol,
            action=signal.action,
            confidence=signal.confidence,
            regime=regime,
            volatility=volatility,
            score=round((signal.confidence * 0.65) + (score * 0.35), 4),
            last_price=signal.last_price,
            risk_notes=risk_notes,
            rationale=[
                *signal.rationale,
                f"Regime={regime.value}",
                f"30-bar realized volatility={volatility:.4f}",
                f"Average 30-bar return={mean(returns[-30:]) if len(returns) >= 30 else 0.0:.5f}",
            ],
        )

    def _regime(self, fast_ema: float, slow_ema: float, momentum: float, volatility: float) -> Regime:
        if volatility > 0.04:
            return Regime.HIGH_VOLATILITY
        if fast_ema > slow_ema and momentum >= 50:
            return Regime.TREND_UP
        if fast_ema < slow_ema and momentum <= 50:
            return Regime.TREND_DOWN
        return Regime.RANGE
