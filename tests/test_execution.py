import asyncio
from datetime import UTC, datetime, timedelta

from app.core.execution import ApprovalBook, ExecutionEngine
from app.core.models import ExecutionResult, MarketType, Side, TradePlan
from app.exchanges.base import Exchange


class DummyExchange(Exchange):
    async def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 120):
        return []

    async def create_order(self, plan: TradePlan) -> ExecutionResult:
        return ExecutionResult(True, "test", plan.symbol, plan.side, plan.amount, "order-1", "ok")

    async def equity(self) -> float:
        return 1000

    async def open_positions(self):
        return []

    async def market_type(self, symbol: str) -> MarketType:
        return MarketType.SPOT


def test_approval_expiry_blocks_execution() -> None:
    async def run() -> None:
        book = ApprovalBook(expiry_minutes=1)
        engine = ExecutionEngine(DummyExchange(), book, approval_required=True)
        plan = TradePlan(
            symbol="BTC/USDT",
            side=Side.BUY,
            amount=1,
            leverage=1,
            entry_price=100,
            stop_loss=90,
            take_profit=120,
            market_type=MarketType.SPOT,
            rationale=[],
            created_at=datetime.now(UTC) - timedelta(minutes=5),
        )
        approval_id = await engine.submit(plan)
        assert isinstance(approval_id, str)
        assert await engine.approve(approval_id) is None

    asyncio.run(run())
