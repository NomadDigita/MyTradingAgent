from __future__ import annotations

from app.core.alpha import AlphaConfluenceEngine
from app.core.backtest import LightweightBacktester
from app.core.models import AgentFinding, Candle, SwarmReport
from app.core.sentinel import BlackSwanSentinel


class TradingSwarm:
    """In-process specialist-agent simulation for explainable trade triage."""

    def __init__(self) -> None:
        self.alpha = AlphaConfluenceEngine()
        self.sentinel = BlackSwanSentinel()
        self.backtester = LightweightBacktester(self.alpha)

    def debate(self, symbol: str, candles: list[Candle]) -> SwarmReport:
        card = self.alpha.card(symbol, candles)
        alert = self.sentinel.evaluate(symbol, candles)
        metrics = self.backtester.run(symbol, candles)
        findings = [
            AgentFinding(
                "DataGuardian",
                "pass" if card.data_quality.valid else "block",
                f"quality={card.data_quality.score:.3f}; {', '.join(card.data_quality.issues[:2])}",
                1.0 - card.data_quality.score,
            ),
            AgentFinding(
                "AlphaDesk",
                card.action.value,
                f"score={card.score:.3f}, confidence={card.confidence:.3f}",
                max(0.0, 1.0 - card.confidence),
            ),
            AgentFinding(
                "Sentinel",
                alert.level.value,
                f"severity={alert.severity:.3f}; {', '.join(alert.triggers[:2])}",
                alert.severity,
            ),
            AgentFinding(
                "BacktestAuditor",
                "diagnostic",
                f"trades={metrics.trades}, win_rate={metrics.win_rate:.2%}, pf={metrics.profit_factor:.2f}",
                min(1.0, metrics.max_drawdown * 2),
            ),
        ]
        if alert.halt_recommended or not card.data_quality.valid:
            decision = "block"
            actions = ["do not create trade plan", "review data source and anomaly state"]
        elif card.action.value != "flat" and card.confidence >= 0.50:
            decision = "watchlist"
            actions = ["eligible for risk engine preflight", "require Telegram approval before execution"]
        else:
            decision = "stand_down"
            actions = ["no high-conviction setup from current evidence"]
        return SwarmReport(symbol, decision, findings, actions)
