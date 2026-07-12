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


class Regime(StrEnum):
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    HIGH_VOLATILITY = "high_volatility"
    UNKNOWN = "unknown"


class AlertLevel(StrEnum):
    INFO = "info"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"


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


@dataclass(frozen=True)
class Position:
    symbol: str
    side: Side
    amount: float
    entry_price: float
    mark_price: float
    leverage: float = 1.0
    market_type: MarketType = MarketType.SPOT

    @property
    def notional(self) -> float:
        return abs(self.amount * self.mark_price)


@dataclass(frozen=True)
class ResearchReport:
    symbol: str
    action: SignalAction
    confidence: float
    regime: Regime
    volatility: float
    score: float
    last_price: float
    risk_notes: list[str]
    rationale: list[str]


@dataclass(frozen=True)
class DataQualityReport:
    symbol: str
    score: float
    valid: bool
    issues: list[str]
    candle_count: int


@dataclass(frozen=True)
class AlphaVote:
    name: str
    direction: float
    confidence: float
    reason: str


@dataclass(frozen=True)
class AlphaCard:
    symbol: str
    score: float
    action: SignalAction
    confidence: float
    votes: list[AlphaVote]
    data_quality: DataQualityReport


@dataclass(frozen=True)
class SentinelAlert:
    symbol: str
    level: AlertLevel
    severity: float
    halt_recommended: bool
    triggers: list[str]


@dataclass(frozen=True)
class BacktestMetrics:
    symbol: str
    trades: int
    win_rate: float
    total_return: float
    max_drawdown: float
    profit_factor: float
    expectancy: float
    sharpe_like: float


@dataclass(frozen=True)
class RiskMetric:
    name: str
    value: float
    limit: float
    passed: bool
    note: str


@dataclass(frozen=True)
class SlippageEstimate:
    symbol: str
    notional: float
    estimated_bps: float
    liquidity_score: float
    notes: list[str]


@dataclass(frozen=True)
class OrderSlice:
    index: int
    amount: float
    notional: float
    delay_seconds: int
    order_type: str


@dataclass(frozen=True)
class OrderRoute:
    symbol: str
    total_amount: float
    total_notional: float
    style: str
    slices: list[OrderSlice]
    slippage: SlippageEstimate
    notes: list[str]


@dataclass(frozen=True)
class ComplianceDecision:
    symbol: str
    approved: bool
    score: float
    metrics: list[RiskMetric]
    blockers: list[str]
    warnings: list[str]


@dataclass(frozen=True)
class AgentFinding:
    agent: str
    status: str
    summary: str
    severity: float


@dataclass(frozen=True)
class SwarmReport:
    symbol: str
    decision: str
    findings: list[AgentFinding]
    recommended_actions: list[str]
