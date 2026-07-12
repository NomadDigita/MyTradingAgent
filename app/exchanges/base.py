from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.models import Candle, ExecutionResult, MarketType, Position, TradePlan


class Exchange(ABC):
    @abstractmethod
    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 120
    ) -> list[Candle]:
        raise NotImplementedError

    @abstractmethod
    async def create_order(self, plan: TradePlan) -> ExecutionResult:
        raise NotImplementedError

    @abstractmethod
    async def equity(self) -> float:
        raise NotImplementedError

    @abstractmethod
    async def open_positions(self) -> list[Position]:
        raise NotImplementedError

    @abstractmethod
    async def market_type(self, symbol: str) -> MarketType:
        raise NotImplementedError
