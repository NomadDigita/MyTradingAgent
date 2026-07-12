from __future__ import annotations

from app.core.models import Regime, ResearchReport, SignalAction
from app.core.research import InstitutionalResearchEngine
from app.exchanges.base import Exchange


class MarketScanner:
    def __init__(self, exchange: Exchange, research: InstitutionalResearchEngine) -> None:
        self.exchange = exchange
        self.research = research

    async def scan(
        self,
        symbols: list[str],
        timeframe: str = "1h",
        limit: int = 120,
    ) -> list[ResearchReport]:
        reports: list[ResearchReport] = []
        for symbol in symbols:
            try:
                candles = await self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                market_type = await self.exchange.market_type(symbol)
                reports.append(self.research.report(symbol, candles, market_type))
            except Exception as exc:  # noqa: BLE001
                reports.append(
                    ResearchReport(
                        symbol=symbol,
                        action=SignalAction.FLAT,
                        confidence=0.0,
                        regime=Regime.UNKNOWN,
                        volatility=0.0,
                        score=0.0,
                        last_price=0.0,
                        risk_notes=[f"scan failed: {exc.__class__.__name__}"],
                        rationale=["Symbol skipped due to adapter error"],
                    )
                )
        return sorted(reports, key=lambda report: report.score, reverse=True)
