from __future__ import annotations

from dataclasses import asdict

import httpx

from app.core.models import TradePlan


class SupabaseTradeStore:
    def __init__(self, url: str, service_role_key: str) -> None:
        self.url = url.rstrip("/")
        self.headers = {
            "apikey": service_role_key,
            "authorization": f"Bearer {service_role_key}",
            "content-type": "application/json",
        }

    async def save_plan(self, plan: TradePlan) -> None:
        payload = asdict(plan)
        payload["side"] = plan.side.value
        payload["market_type"] = plan.market_type.value
        payload["created_at"] = plan.created_at.isoformat()
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.url}/rest/v1/trade_plans",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
