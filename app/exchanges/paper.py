from __future__ import annotations

import itertools
import random
import time

from app.core.models import Candle, ExecutionResult, MarketType, TradePlan
from app.exchanges.base import Exchange


class PaperExchange(Exchange):
    def __init__(self, starting_equity: float = 10_000.0) -> None:
        self._equity = starting_equity
        self._ids = itertools.count(1)

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 120
    ) -> list[Candle]:
        del timeframe
        base = 100.0 + (abs(hash(symbol)) % 5000)
        now = int(time.time() * 1000)
        candles: list[Candle] = []
        price = base
        for index in range(limit):
            drift = random.uniform(-0.012, 0.012)
            open_price = price
            close = max(0.01, open_price * (1 + drift))
            high = max(open_price, close) * (1 + random.uniform(0, 0.006))
            low = min(open_price, close) * (1 - random.uniform(0, 0.006))
            candles.append(
                Candle(
                    timestamp=now - ((limit - index) * 60 * 60 * 1000),
                    open=open_price,
                    high=high,
                    low=low,
                    close=close,
                    volume=random.uniform(100, 10_000),
                )
            )
            price = close
        return candles

    async def create_order(self, plan: TradePlan) -> ExecutionResult:
        return ExecutionResult(
            ok=True,
            mode="paper",
            symbol=plan.symbol,
            side=plan.side,
            amount=plan.amount,
            order_id=f"paper-{next(self._ids)}",
            message=f"Paper order accepted at notional {plan.notional:.2f}",
        )

    async def equity(self) -> float:
        return self._equity

    async def market_type(self, symbol: str) -> MarketType:
        if ":" in symbol or symbol.endswith(".P"):
            return MarketType.SWAP
        return MarketType.SPOT
