from __future__ import annotations

from dataclasses import dataclass

from app.core.models import Position


@dataclass(frozen=True)
class PortfolioSnapshot:
    equity: float
    positions: list[Position]

    @property
    def gross_notional(self) -> float:
        return sum(position.notional for position in self.positions)

    @property
    def net_notional(self) -> float:
        return sum(position.amount * position.mark_price for position in self.positions)

    @property
    def exposure_by_symbol(self) -> dict[str, float]:
        exposure: dict[str, float] = {}
        for position in self.positions:
            exposure[position.symbol] = exposure.get(position.symbol, 0.0) + position.notional
        return exposure

    @property
    def gross_leverage(self) -> float:
        if self.equity <= 0:
            return 0.0
        return self.gross_notional / self.equity

    def risk_summary(self) -> list[str]:
        return [
            f"Equity: {self.equity:.2f}",
            f"Open positions: {len(self.positions)}",
            f"Gross notional: {self.gross_notional:.2f}",
            f"Net notional: {self.net_notional:.2f}",
            f"Gross leverage: {self.gross_leverage:.2f}x",
        ]
