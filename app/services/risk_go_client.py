from __future__ import annotations

import httpx


class GoRiskClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    async def dynamic_leverage(self, confidence: float, max_leverage: float) -> float:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(
                f"{self.base_url}/leverage",
                json={"confidence": confidence, "max_leverage": max_leverage},
            )
            response.raise_for_status()
            return float(response.json()["leverage"])
