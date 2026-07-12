from __future__ import annotations

from statistics import pstdev

from app.core.correlation import returns
from app.core.models import Candle, Position, RiskMetric


class HistoricalVaREngine:
    """Simple historical/parametric VaR gate for portfolio-level pre-trade checks."""

    def metric(
        self,
        candles: list[Candle],
        equity: float,
        current_positions: list[Position],
        candidate_notional: float,
        max_var_pct: float = 0.08,
        confidence_z: float = 1.65,
    ) -> RiskMetric:
        series = returns(candles)
        if len(series) < 20 or equity <= 0:
            return RiskMetric("portfolio_var_pct", 0.0, max_var_pct, True, "insufficient data; VaR skipped")
        vol = pstdev(series[-60:])
        gross_notional = sum(position.notional for position in current_positions) + candidate_notional
        one_period_var = gross_notional * vol * confidence_z
        value = one_period_var / equity
        return RiskMetric(
            name="portfolio_var_pct",
            value=round(value, 4),
            limit=max_var_pct,
            passed=value <= max_var_pct,
            note="parametric 95% one-period VaR over gross notional",
        )
