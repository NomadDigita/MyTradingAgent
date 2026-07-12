from __future__ import annotations

from statistics import mean, pstdev

from app.core.alpha import AlphaConfluenceEngine
from app.core.models import BacktestMetrics, Candle, SignalAction


class LightweightBacktester:
    """Fast deterministic walk-forward backtester for sanity checks."""

    def __init__(self, engine: AlphaConfluenceEngine | None = None) -> None:
        self.engine = engine or AlphaConfluenceEngine()

    def run(self, symbol: str, candles: list[Candle], window: int = 80, fee_bps: float = 6.0) -> BacktestMetrics:
        if len(candles) <= window + 2:
            return BacktestMetrics(symbol, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        equity = 1.0
        peak = equity
        max_drawdown = 0.0
        trade_returns: list[float] = []
        fee = fee_bps / 10_000

        for index in range(window, len(candles) - 1):
            card = self.engine.card(symbol, candles[index - window : index])
            entry = candles[index].close
            exit_price = candles[index + 1].close
            if card.action == SignalAction.FLAT or entry <= 0:
                continue
            raw_return = exit_price / entry - 1
            if card.action == SignalAction.SHORT:
                raw_return *= -1
            strategy_return = raw_return - (fee * 2)
            trade_returns.append(strategy_return)
            equity *= 1 + strategy_return
            peak = max(peak, equity)
            drawdown = (peak - equity) / peak if peak else 0.0
            max_drawdown = max(max_drawdown, drawdown)

        wins = [item for item in trade_returns if item > 0]
        losses = [abs(item) for item in trade_returns if item <= 0]
        profit_factor = sum(wins) / sum(losses) if losses and sum(losses) > 0 else float(len(wins) > 0)
        volatility = pstdev(trade_returns) if len(trade_returns) >= 2 else 0.0
        expectancy = mean(trade_returns) if trade_returns else 0.0
        sharpe_like = (expectancy / volatility) if volatility else 0.0
        return BacktestMetrics(
            symbol=symbol,
            trades=len(trade_returns),
            win_rate=round(len(wins) / len(trade_returns), 4) if trade_returns else 0.0,
            total_return=round(equity - 1, 4),
            max_drawdown=round(max_drawdown, 4),
            profit_factor=round(profit_factor, 4),
            expectancy=round(expectancy, 6),
            sharpe_like=round(sharpe_like, 4),
        )
