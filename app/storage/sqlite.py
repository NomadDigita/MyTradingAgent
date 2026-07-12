from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.core.models import TradePlan


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
        self.connection.commit()

    def save_plan(self, plan: TradePlan) -> None:
        payload = {
            "symbol": plan.symbol,
            "side": plan.side.value,
            "amount": plan.amount,
            "leverage": plan.leverage,
            "entry_price": plan.entry_price,
            "stop_loss": plan.stop_loss,
            "take_profit": plan.take_profit,
            "market_type": plan.market_type.value,
            "rationale": plan.rationale,
        }
        self.connection.execute(
            "insert or replace into trade_plans values (?, ?, ?)",
            (plan.approval_id, json.dumps(payload), plan.created_at.isoformat()),
        )
        self.connection.commit()
