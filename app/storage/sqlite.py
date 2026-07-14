from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.core.models import ExecutionResult, TradePlan
from app.storage.base import dumps, execution_payload, plan_payload


class SQLiteTradeStore:
    def __init__(self, url: str) -> None:
        path = url.removeprefix("sqlite:///")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """
            create table if not exists trade_plans (
                approval_id text primary key,
                payload text not null,
                created_at text not null
            )
            """
        )
        self.connection.execute(
            """
            create table if not exists trade_executions (
                id integer primary key autoincrement,
                approval_id text,
                event_type text not null,
                payload text not null,
                created_at text not null
            )
            """
        )
        self.connection.commit()

    async def save_plan(self, plan: TradePlan) -> None:
        self.connection.execute(
            "insert or replace into trade_plans values (?, ?, ?)",
            (plan.approval_id, json.dumps(plan_payload(plan)), plan.created_at.isoformat()),
        )
        self.connection.commit()

    async def save_execution(
        self,
        approval_id: str | None,
        result: ExecutionResult,
        event_type: str,
    ) -> None:
        self.connection.execute(
            """
            insert into trade_executions (approval_id, event_type, payload, created_at)
            values (?, ?, ?, ?)
            """,
            (
                approval_id,
                event_type,
                dumps(execution_payload(result)),
                datetime.now(UTC).isoformat(),
            ),
        )
        self.connection.commit()
