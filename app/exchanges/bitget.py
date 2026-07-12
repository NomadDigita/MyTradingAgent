from __future__ import annotations

import asyncio
from typing import Any

from app.core.models import Candle, ExecutionResult, MarketType, Position, Side, TradePlan
from app.exchanges.base import Exchange


class BitgetExchange(Exchange):
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        api_password: str,
        sandbox: bool = False,
    ) -> None:
        try:
            import ccxt  # type: ignore
        except ImportError as exc:
            raise RuntimeError("ccxt is required for live Bitget trading") from exc

        self._exchange = ccxt.bitget(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "password": api_password,
                "enableRateLimit": True,
                "options": {"defaultType": "swap"},
            }
        )
        if sandbox:
            self._exchange.set_sandbox_mode(True)

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 120
    ) -> list[Candle]:
        rows = await asyncio.to_thread(self._exchange.fetch_ohlcv, symbol, timeframe, None, limit)
        return [
            Candle(
                timestamp=int(row[0]),
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=float(row[5]),
            )
            for row in rows
        ]

    async def create_order(self, plan: TradePlan) -> ExecutionResult:
        params: dict[str, Any] = {}
        if plan.market_type in {MarketType.FUTURE, MarketType.SWAP}:
            await asyncio.to_thread(self._exchange.set_leverage, int(plan.leverage), plan.symbol)
        if plan.stop_loss:
            params["stopLoss"] = {"triggerPrice": plan.stop_loss}
        if plan.take_profit:
            params["takeProfit"] = {"triggerPrice": plan.take_profit}
        order = await asyncio.to_thread(
            self._exchange.create_market_order,
            plan.symbol,
            plan.side.value,
            plan.amount,
            None,
            params,
        )
        return ExecutionResult(
            ok=True,
            mode="live",
            symbol=plan.symbol,
            side=plan.side,
            amount=plan.amount,
            order_id=str(order.get("id") or order.get("clientOrderId") or ""),
            message="Live Bitget order submitted",
        )

    async def equity(self) -> float:
        balance = await asyncio.to_thread(self._exchange.fetch_balance)
        total = balance.get("total", {})
        usdt = total.get("USDT")
        if usdt is None:
            return 0.0
        return float(usdt)

    async def open_positions(self) -> list[Position]:
        if not getattr(self._exchange, "has", {}).get("fetchPositions"):
            return []
        rows = await asyncio.to_thread(self._exchange.fetch_positions)
        positions: list[Position] = []
        for row in rows:
            contracts = float(row.get("contracts") or row.get("contractSize") or 0)
            if contracts == 0:
                continue
            side_raw = str(row.get("side") or "").lower()
            side = Side.SELL if side_raw == "short" else Side.BUY
            mark = float(row.get("markPrice") or row.get("lastPrice") or row.get("entryPrice") or 0)
            entry = float(row.get("entryPrice") or mark or 0)
            leverage = float(row.get("leverage") or 1)
            symbol = str(row.get("symbol") or "")
            market_type = await self.market_type(symbol) if symbol else MarketType.SWAP
            positions.append(
                Position(
                    symbol=symbol,
                    side=side,
                    amount=contracts if side == Side.BUY else -contracts,
                    entry_price=entry,
                    mark_price=mark,
                    leverage=leverage,
                    market_type=market_type,
                )
            )
        return positions

    async def market_type(self, symbol: str) -> MarketType:
        markets = await asyncio.to_thread(self._exchange.load_markets)
        market = markets.get(symbol, {})
        if market.get("spot"):
            return MarketType.SPOT
        if market.get("swap"):
            return MarketType.SWAP
        if market.get("future"):
            return MarketType.FUTURE
        return MarketType.SPOT
