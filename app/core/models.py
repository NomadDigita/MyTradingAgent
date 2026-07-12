from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class MarketType(StrEnum):
    SPOT = "spot"
    FUTURE = "future"
    SWAP = "swap"
    CFD = "cfd"
    STOCK = "stock"


class SignalAction(StrEnum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


@dataclass(frozen=True)
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    symbol: str
    action: SignalAction
    confidence: float
    rationale: list[str]
    stop_loss: float | None
    take_profit: float | None
    last_price: float
    market_type: MarketType = MarketType.SPOT


@dataclass(frozen=True)
class TradePlan:
    symbol: str
    side: Side
    amount: float
    leverage: float
    entry_price: float
    stop_loss: float | None
    take_profit: float | None
    market_type: MarketType
    rationale: list[str]
    approval_id: str = field(default_factory=lambda: uuid4().hex[:10])
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def notional(self) -> float:
        return self.amount * self.entry_price


@dataclass
class ExecutionResult:
    ok: bool
    mode: str
    symbol: str
    side: Side
    amount: float
    order_id: str | None = None
    message: str = ""
