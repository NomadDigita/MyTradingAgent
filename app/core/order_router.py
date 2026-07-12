from __future__ import annotations

from app.core.models import OrderRoute, OrderSlice, TradePlan
from app.core.slippage import LiquiditySlippageModel


class SmartOrderRouter:
    """Creates an execution route; actual exchange execution remains approval-gated."""

    def __init__(self, slippage_model: LiquiditySlippageModel | None = None) -> None:
        self.slippage_model = slippage_model or LiquiditySlippageModel()

    def route(self, plan: TradePlan, candles, max_slice_notional: float = 50.0) -> OrderRoute:
        slippage = self.slippage_model.estimate(plan.symbol, candles, plan.notional)
        if plan.notional <= max_slice_notional and slippage.estimated_bps < 25:
            style = "single_market"
            slice_count = 1
            notes = ["single slice due to low notional and acceptable estimated slippage"]
        elif slippage.liquidity_score < 0.35:
            style = "twap_defensive"
            slice_count = min(10, max(3, int(plan.notional // max_slice_notional) + 1))
            notes = ["defensive TWAP route due to weak liquidity score"]
        else:
            style = "twap_standard"
            slice_count = min(6, max(2, int(plan.notional // max_slice_notional) + 1))
            notes = ["standard TWAP route to reduce market impact"]

        amount_per_slice = plan.amount / slice_count
        slices = [
            OrderSlice(
                index=index + 1,
                amount=round(amount_per_slice, 8),
                notional=round(amount_per_slice * plan.entry_price, 4),
                delay_seconds=index * 20,
                order_type="market" if style == "single_market" else "limit_or_marketable_limit",
            )
            for index in range(slice_count)
        ]
        return OrderRoute(
            symbol=plan.symbol,
            total_amount=plan.amount,
            total_notional=plan.notional,
            style=style,
            slices=slices,
            slippage=slippage,
            notes=notes,
        )
