from __future__ import annotations

from dataclasses import dataclass

from app.core.models import Position, Side, Signal, SignalAction, TradePlan


@dataclass(frozen=True)
class RiskConfig:
    max_leverage: float = 20.0
    default_risk_per_trade: float = 0.005
    max_notional_per_trade: float = 100.0
    max_daily_loss: float = 50.0
    max_open_positions: int = 5
    max_symbol_notional: float = 250.0
    max_portfolio_notional: float = 500.0
    min_signal_confidence: float = 0.55
    require_stop_loss: bool = True


@dataclass(frozen=True)
class RiskState:
    equity: float
    realized_pnl_today: float = 0.0
    open_positions: list[Position] | None = None
    trading_halted: bool = False


class RiskEngine:
    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    def build_plan(self, signal: Signal, state: RiskState) -> TradePlan | None:
        if state.trading_halted:
            return None
        if signal.action == SignalAction.FLAT or signal.confidence < self.config.min_signal_confidence:
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
        plan = TradePlan(
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
        if self.validate_plan(plan, state):
            return None
        return plan

    def dynamic_leverage(self, confidence: float) -> float:
        capped_confidence = min(max(confidence, 0.0), 1.0)
        raw = 1.0 + (capped_confidence - 0.55) * 30
        return round(min(max(raw, 1.0), self.config.max_leverage, 20.0), 2)

    def validate_plan(self, plan: TradePlan, state: RiskState | None = None) -> list[str]:
        errors: list[str] = []
        if plan.leverage > min(self.config.max_leverage, 20.0):
            errors.append("leverage exceeds configured maximum")
        if plan.notional > self.config.max_notional_per_trade:
            errors.append("notional exceeds per-trade maximum")
        if plan.amount <= 0:
            errors.append("amount must be positive")
        if plan.entry_price <= 0:
            errors.append("entry price must be positive")
        if self.config.require_stop_loss and plan.stop_loss is None:
            errors.append("stop loss is required")
        if state is not None:
            if state.trading_halted:
                errors.append("trading is halted by operator kill switch")
            if state.realized_pnl_today <= -abs(self.config.max_daily_loss):
                errors.append("daily loss limit reached")
            open_positions = state.open_positions or []
            if len(open_positions) >= self.config.max_open_positions:
                errors.append("maximum open position count reached")
            symbol_notional = sum(p.notional for p in open_positions if p.symbol == plan.symbol)
            if symbol_notional + plan.notional > self.config.max_symbol_notional:
                errors.append("symbol notional exposure limit exceeded")
            portfolio_notional = sum(p.notional for p in open_positions)
            if portfolio_notional + plan.notional > self.config.max_portfolio_notional:
                errors.append("portfolio notional exposure limit exceeded")
        return errors
