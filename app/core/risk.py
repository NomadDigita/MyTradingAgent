from __future__ import annotations

from dataclasses import dataclass

from app.core.models import Side, Signal, SignalAction, TradePlan


@dataclass(frozen=True)
class RiskConfig:
    max_leverage: float = 20.0
    default_risk_per_trade: float = 0.005
    max_notional_per_trade: float = 100.0
    max_daily_loss: float = 50.0


@dataclass(frozen=True)
class RiskState:
    equity: float
    realized_pnl_today: float = 0.0


class RiskEngine:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def build_plan(self, signal: Signal, state: RiskState) -> TradePlan | None:
        if signal.action == SignalAction.FLAT or signal.confidence < 0.55:
            return None
        if abs(state.realized_pnl_today) >= self.config.max_daily_loss and state.realized_pnl_today < 0:
            return None

        leverage = self.dynamic_leverage(signal.confidence)
        risk_budget = state.equity * self.config.default_risk_per_trade
        notional = min(risk_budget * leverage, self.config.max_notional_per_trade)
        if signal.last_price <= 0 or notional <= 0:
            return None

        amount = notional / signal.last_price
        side = Side.BUY if signal.action == SignalAction.LONG else Side.SELL
        return TradePlan(
            symbol=signal.symbol,
            side=side,
            amount=round(amount, 8),
            leverage=leverage,
            entry_price=signal.last_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            market_type=signal.market_type,
            rationale=signal.rationale,
        )

    def dynamic_leverage(self, confidence: float) -> float:
        capped_confidence = min(max(confidence, 0.0), 1.0)
        raw = 1.0 + (capped_confidence - 0.55) * 30
        return round(min(max(raw, 1.0), self.config.max_leverage, 20.0), 2)

    def validate_plan(self, plan: TradePlan) -> list[str]:
        errors: list[str] = []
        if plan.leverage > min(self.config.max_leverage, 20.0):
            errors.append("leverage exceeds configured maximum")
        if plan.notional > self.config.max_notional_per_trade:
            errors.append("notional exceeds per-trade maximum")
        if plan.amount <= 0:
            errors.append("amount must be positive")
        if plan.entry_price <= 0:
            errors.append("entry price must be positive")
        return errors
