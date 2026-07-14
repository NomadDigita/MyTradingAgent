from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.core.audit import AuditJournal
from app.core.models import ExecutionResult, TradePlan
from app.exchanges.base import Exchange
from app.storage.base import NullTradeStore, TradeStore


@dataclass
class ApprovalBook:
    pending: dict[str, TradePlan] = field(default_factory=dict)
    expiry_minutes: int = 15

    def add(self, plan: TradePlan) -> str:
        self.pending[plan.approval_id] = plan
        return plan.approval_id

    def pop(self, approval_id: str) -> TradePlan | None:
        plan = self.pending.pop(approval_id, None)
        if plan is None:
            return None
        if datetime.now(UTC) - plan.created_at > timedelta(minutes=self.expiry_minutes):
            return None
        return plan

    def reject(self, approval_id: str) -> bool:
        return self.pending.pop(approval_id, None) is not None

    def prune_expired(self) -> list[str]:
        now = datetime.now(UTC)
        expired = [
            approval_id
            for approval_id, plan in self.pending.items()
            if now - plan.created_at > timedelta(minutes=self.expiry_minutes)
        ]
        for approval_id in expired:
            self.pending.pop(approval_id, None)
        return expired


class ExecutionEngine:
    def __init__(
        self,
        exchange: Exchange,
        approval_book: ApprovalBook,
        approval_required: bool,
        audit: AuditJournal | None = None,
        store: TradeStore | None = None,
    ) -> None:
        self.exchange = exchange
        self.approval_book = approval_book
        self.approval_required = approval_required
        self.audit = audit
        self.store = store or NullTradeStore()

    async def submit(self, plan: TradePlan) -> ExecutionResult | str:
        await self._save_plan(plan)
        if self.approval_required:
            approval_id = self.approval_book.add(plan)
            self._record("approval_created", {"approval_id": approval_id, "plan": plan})
            return approval_id
        result = await self.exchange.create_order(plan)
        await self._save_execution(None, result, "order_executed_without_approval")
        self._record("order_executed_without_approval", {"plan": plan, "result": result})
        return result

    async def approve(self, approval_id: str) -> ExecutionResult | None:
        plan = self.approval_book.pop(approval_id)
        if plan is None:
            self._record("approval_missing_or_expired", {"approval_id": approval_id})
            return None
        result = await self.exchange.create_order(plan)
        await self._save_execution(approval_id, result, "approval_executed")
        self._record("approval_executed", {"approval_id": approval_id, "plan": plan, "result": result})
        return result

    def reject(self, approval_id: str) -> bool:
        rejected = self.approval_book.reject(approval_id)
        self._record("approval_rejected", {"approval_id": approval_id, "rejected": rejected})
        return rejected

    def _record(self, event_type: str, payload: dict) -> None:
        if self.audit is not None:
            self.audit.record(event_type, payload)

    async def _save_plan(self, plan: TradePlan) -> None:
        try:
            await self.store.save_plan(plan)
        except Exception as exc:  # noqa: BLE001
            self._record("storage_save_plan_failed", {"approval_id": plan.approval_id, "error": str(exc)})

    async def _save_execution(
        self,
        approval_id: str | None,
        result: ExecutionResult,
        event_type: str,
    ) -> None:
        try:
            await self.store.save_execution(approval_id, result, event_type)
        except Exception as exc:  # noqa: BLE001
            self._record("storage_save_execution_failed", {"approval_id": approval_id, "error": str(exc)})
