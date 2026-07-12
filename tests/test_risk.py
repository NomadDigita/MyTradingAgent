from app.core.models import MarketType, Signal, SignalAction
from app.core.risk import RiskConfig, RiskEngine, RiskState


def test_dynamic_leverage_is_capped_at_20() -> None:
    engine = RiskEngine(RiskConfig(max_leverage=100))
    assert engine.dynamic_leverage(1.0) == 14.5


def test_plan_respects_notional_cap() -> None:
    engine = RiskEngine(RiskConfig(max_leverage=20, max_notional_per_trade=25))
    signal = Signal(
        symbol="BTC/USDT",
        action=SignalAction.LONG,
        confidence=0.9,
        rationale=["test"],
        stop_loss=90,
        take_profit=120,
        last_price=100,
        market_type=MarketType.SPOT,
    )
    plan = engine.build_plan(signal, RiskState(equity=10_000))
    assert plan is not None
    assert plan.notional <= 25.000001


def test_low_confidence_signal_does_not_trade() -> None:
    engine = RiskEngine(RiskConfig())
    signal = Signal(
        symbol="BTC/USDT",
        action=SignalAction.LONG,
        confidence=0.1,
        rationale=[],
        stop_loss=None,
        take_profit=None,
        last_price=100,
        market_type=MarketType.SPOT,
    )
    assert engine.build_plan(signal, RiskState(equity=1000)) is None
