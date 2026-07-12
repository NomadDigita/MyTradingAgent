from app.core.compliance import PreTradeComplianceEngine
from app.core.models import Candle, MarketType, Side, TradePlan
from app.core.order_router import SmartOrderRouter
from app.core.playbook import IncidentPlaybook
from app.core.slippage import LiquiditySlippageModel
from app.core.swarm import TradingSwarm
from app.core.var import HistoricalVaREngine


def _candles(count: int = 140) -> list[Candle]:
    price = 100.0
    rows: list[Candle] = []
    for index in range(count):
        price *= 1.0008
        rows.append(
            Candle(
                timestamp=index * 60_000,
                open=price * 0.999,
                high=price * 1.004,
                low=price * 0.997,
                close=price,
                volume=5000 + index * 3,
            )
        )
    return rows


def _plan() -> TradePlan:
    return TradePlan(
        symbol="BTC/USDT",
        side=Side.BUY,
        amount=0.2,
        leverage=2,
        entry_price=100,
        stop_loss=95,
        take_profit=110,
        market_type=MarketType.SPOT,
        rationale=["test"],
    )


def test_var_metric_passes_for_small_notional() -> None:
    metric = HistoricalVaREngine().metric(_candles(), equity=10_000, current_positions=[], candidate_notional=20)
    assert metric.name == "portfolio_var_pct"
    assert metric.passed


def test_slippage_model_returns_bps_and_liquidity_score() -> None:
    estimate = LiquiditySlippageModel().estimate("BTC/USDT", _candles(), notional=50)
    assert estimate.estimated_bps > 0
    assert 0 <= estimate.liquidity_score <= 1


def test_order_router_slices_large_order() -> None:
    plan = _plan()
    route = SmartOrderRouter().route(plan, _candles(), max_slice_notional=5)
    assert len(route.slices) > 1
    assert route.total_notional == plan.notional


def test_compliance_engine_returns_decision() -> None:
    decision = PreTradeComplianceEngine().check(_plan(), _candles(), equity=10_000, positions=[])
    assert decision.symbol == "BTC/USDT"
    assert decision.metrics


def test_swarm_report_has_specialist_findings() -> None:
    report = TradingSwarm().debate("BTC/USDT", _candles())
    assert len(report.findings) == 4
    assert report.decision in {"block", "watchlist", "stand_down"}


def test_playbook_lists_available_items() -> None:
    text = IncidentPlaybook().render("")
    assert "Available playbooks" in text
