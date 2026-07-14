from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Protocol

from app.core.models import ExecutionResult, TradePlan


class TradeStore(Protocol):
    async def save_plan(self, plan: TradePlan) -> None:
        raise NotImplementedError

    async def save_execution(
        self,
        approval_id: str | None,
        result: ExecutionResult,
        event_type: str,
    ) -> None:
        raise NotImplementedError


class NullTradeStore:
    async def save_plan(self, plan: TradePlan) -> None:
        return None

    async def save_execution(
        self,
        approval_id: str | None,
        result: ExecutionResult,
        event_type: str,
    ) -> None:
        return None


def plan_payload(plan: TradePlan) -> dict[str, Any]:
    payload = _json_safe(asdict(plan))
    payload["side"] = plan.side.value
    payload["market_type"] = plan.market_type.value
    payload["created_at"] = plan.created_at.isoformat()
    return payload


def execution_payload(result: ExecutionResult) -> dict[str, Any]:
    return _json_safe(asdict(result))


def dumps(value: Any) -> str:
    return json.dumps(_json_safe(value), sort_keys=True)


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value
