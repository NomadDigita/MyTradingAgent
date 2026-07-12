from __future__ import annotations

import math
from statistics import mean

from app.core.models import Candle, Position, RiskMetric


def returns(candles: list[Candle]) -> list[float]:
    return [
        current.close / previous.close - 1
        for previous, current in zip(candles, candles[1:], strict=False)
        if previous.close
    ]


def pearson(left: list[float], right: list[float]) -> float:
    size = min(len(left), len(right))
    if size < 3:
        return 0.0
    x = left[-size:]
    y = right[-size:]
    mx = mean(x)
    my = mean(y)
    numerator = sum((a - mx) * (b - my) for a, b in zip(x, y, strict=False))
    dx = math.sqrt(sum((a - mx) ** 2 for a in x))
    dy = math.sqrt(sum((b - my) ** 2 for b in y))
    if dx == 0 or dy == 0:
        return 0.0
    return max(-1.0, min(1.0, numerator / (dx * dy)))


class CorrelationRiskEngine:
    def concentration_metric(
        self,
        candidate_symbol: str,
        candidate_returns: list[float],
        open_positions: list[Position],
        market_returns: dict[str, list[float]],
        max_average_correlation: float = 0.75,
    ) -> RiskMetric:
        correlations: list[float] = []
        for position in open_positions:
            series = market_returns.get(position.symbol)
            if series:
                correlations.append(abs(pearson(candidate_returns, series)))
        value = mean(correlations) if correlations else 0.0
        return RiskMetric(
            name="average_abs_position_correlation",
            value=round(value, 4),
            limit=max_average_correlation,
            passed=value <= max_average_correlation,
            note=f"{candidate_symbol} average absolute correlation versus open book",
        )
