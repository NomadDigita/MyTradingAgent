import asyncio
import sqlite3

from app.core.execution import ApprovalBook, ExecutionEngine
from app.core.models import ExecutionResult, MarketType, Side, TradePlan
from app.exchanges.base import Exchange
from app.storage.sqlite import SQLiteTradeStore


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


def test_execution_engine_persists_plan_and_execution_to_sqlite(tmp_path) -> None:
    async def run() -> None:
        db_path = tmp_path / "agent.sqlite"
        store = SQLiteTradeStore(f"sqlite:///{db_path}")
        engine = ExecutionEngine(
            DummyExchange(),
            ApprovalBook(),
            approval_required=True,
            store=store,
        )
        plan = TradePlan(
            symbol="BTC/USDT",
            side=Side.BUY,
            amount=1,
            leverage=1,
            entry_price=100,
            stop_loss=90,
            take_profit=120,
            market_type=MarketType.SPOT,
            rationale=["test"],
        )
        approval_id = await engine.submit(plan)
        assert isinstance(approval_id, str)
        await engine.approve(approval_id)

        connection = sqlite3.connect(db_path)
        plan_count = connection.execute("select count(*) from trade_plans").fetchone()[0]
        execution_count = connection.execute("select count(*) from trade_executions").fetchone()[0]
        assert plan_count == 1
        assert execution_count == 1

    asyncio.run(run())
