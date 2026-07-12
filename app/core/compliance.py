from __future__ import annotations

from app.core.alpha import AlphaConfluenceEngine
from app.core.correlation import CorrelationRiskEngine, returns
from app.core.models import Candle, ComplianceDecision, Position, RiskMetric, TradePlan
from app.core.sentinel import BlackSwanSentinel
from app.core.slippage import LiquiditySlippageModel
from app.core.var import HistoricalVaREngine


class PreTradeComplianceEngine:
    """Aggregates institutional pre-trade checks into one decision."""

    def __init__(self) -> None:
        self.alpha = AlphaConfluenceEngine()
        self.sentinel = BlackSwanSentinel()
        self.var = HistoricalVaREngine()
        self.correlation = CorrelationRiskEngine()
        self.slippage = LiquiditySlippageModel()

    def check(
        self,
        plan: TradePlan,
        candles: list[Candle],
        equity: float,
        positions: list[Position],
        market_returns: dict[str, list[float]] | None = None,
    ) -> ComplianceDecision:
        market_returns = market_returns or {}
        metrics: list[RiskMetric] = []
        blockers: list[str] = []
        warnings: list[str] = []

        quality = self.alpha.card(plan.symbol, candles).data_quality
        metrics.append(RiskMetric("data_quality", quality.score, 0.70, quality.valid, "; ".join(quality.issues)))
        if not quality.valid:
            blockers.append("data quality gate failed")

        alert = self.sentinel.evaluate(plan.symbol, candles)
        metrics.append(
            RiskMetric("sentinel_severity", alert.severity, 0.80, not alert.halt_recommended, "; ".join(alert.triggers))
        )
        if alert.halt_recommended:
            blockers.append("black-swan sentinel recommends halt")
        elif alert.severity >= 0.55:
            warnings.append("sentinel warning severity active")

        metrics.append(self.var.metric(candles, equity, positions, plan.notional))
        candidate_returns = returns(candles)
        metrics.append(
            self.correlation.concentration_metric(
                plan.symbol,
                candidate_returns,
                positions,
                market_returns,
            )
        )

        slippage = self.slippage.estimate(plan.symbol, candles, plan.notional)
        slippage_passed = slippage.estimated_bps <= 75 and slippage.liquidity_score >= 0.20
        metrics.append(
            RiskMetric(
                "estimated_slippage_bps",
                slippage.estimated_bps,
                75.0,
                slippage_passed,
                "; ".join(slippage.notes),
            )
        )
        if not slippage_passed:
            blockers.append("slippage/liquidity gate failed")

        failed_metrics = [metric for metric in metrics if not metric.passed]
        score = round(sum(1 for metric in metrics if metric.passed) / max(len(metrics), 1), 4)
        blockers.extend(metric.name for metric in failed_metrics if metric.name not in {"sentinel_severity"})
        return ComplianceDecision(
            symbol=plan.symbol,
            approved=not blockers,
            score=score,
            metrics=metrics,
            blockers=sorted(set(blockers)),
            warnings=warnings,
        )
