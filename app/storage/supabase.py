from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.models import ExecutionResult, TradePlan
from app.storage.base import execution_payload, plan_payload


class SupabaseTradeStore:
    def __init__(self, url: str, secret_key: str) -> None:
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": secret_key,
            "authorization": f"Bearer {secret_key}",
            "content-type": "application/json",
        }

    async def save_plan(self, plan: TradePlan) -> None:
        payload = {
            "approval_id": plan.approval_id,
            "payload": plan_payload(plan),
            "created_at": plan.created_at.isoformat(),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.url}/rest/v1/trade_plans",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()

    async def save_execution(
        self,
        approval_id: str | None,
        result: ExecutionResult,
        event_type: str,
    ) -> None:
        payload = {
            "approval_id": approval_id,
            "event_type": event_type,
            "payload": execution_payload(result),
            "created_at": datetime.now(UTC).isoformat(),
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.url}/rest/v1/trade_executions",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
