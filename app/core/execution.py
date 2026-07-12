from __future__ import annotations

from dataclasses import dataclass, field

from app.core.models import ExecutionResult, TradePlan
from app.exchanges.base import Exchange


@dataclass
class ApprovalBook:
    pending: dict[str, TradePlan] = field(default_factory=dict)

    def add(self, plan: TradePlan) -> str:
        self.pending[plan.approval_id] = plan
        return plan.approval_id

    def pop(self, approval_id: str) -> TradePlan | None:
        return self.pending.pop(approval_id, None)

    def reject(self, approval_id: str) -> bool:
        return self.pending.pop(approval_id, None) is not None


class ExecutionEngine:
    def __init__(self, exchange: Exchange, approval_book: ApprovalBook, approval_required: bool) -> None:
        self.exchange = exchange
        self.approval_book = approval_book
        self.approval_required = approval_required

    async def submit(self, plan: TradePlan) -> ExecutionResult | str:
        if self.approval_required:
            return self.approval_book.add(plan)
        return await self.exchange.create_order(plan)

    async def approve(self, approval_id: str) -> ExecutionResult | None:
        plan = self.approval_book.pop(approval_id)
        if plan is None:
            return None
        return await self.exchange.create_order(plan)
