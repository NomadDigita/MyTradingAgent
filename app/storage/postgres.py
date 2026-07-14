from __future__ import annotations

from datetime import UTC, datetime

from app.core.models import ExecutionResult, TradePlan
from app.storage.base import dumps, execution_payload, plan_payload


class PostgresTradeStore:
    """Supabase direct Postgres storage using the dashboard connection string."""

    def __init__(self, direct_database_url: str) -> None:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg[binary] is required for Supabase direct Postgres storage") from exc
        self._psycopg = psycopg
        self.direct_database_url = direct_database_url
        self._ensure_schema()

    async def save_plan(self, plan: TradePlan) -> None:
        with self._psycopg.connect(self.direct_database_url) as connection:
            connection.execute(
                """
                insert into trade_plans (approval_id, payload, created_at)
                values (%s, %s::jsonb, %s)
                on conflict (approval_id) do update
                set payload = excluded.payload,
                    created_at = excluded.created_at
                """,
                (plan.approval_id, dumps(plan_payload(plan)), plan.created_at),
            )

    async def save_execution(
        self,
        approval_id: str | None,
        result: ExecutionResult,
        event_type: str,
    ) -> None:
        with self._psycopg.connect(self.direct_database_url) as connection:
            connection.execute(
                """
                insert into trade_executions (approval_id, event_type, payload, created_at)
                values (%s, %s, %s::jsonb, %s)
                """,
                (
                    approval_id,
                    event_type,
                    dumps(execution_payload(result)),
                    datetime.now(UTC),
                ),
            )

    def _ensure_schema(self) -> None:
        with self._psycopg.connect(self.direct_database_url) as connection:
            connection.execute(
                """
                create table if not exists trade_plans (
                    approval_id text primary key,
                    payload jsonb not null,
                    created_at timestamptz not null
                )
                """
            )
            connection.execute(
                """
                create table if not exists trade_executions (
                    id bigserial primary key,
                    approval_id text,
                    event_type text not null,
                    payload jsonb not null,
                    created_at timestamptz not null
                )
                """
            )
