from app.core.models import MarketType, Signal, SignalAction
from app.core.models import Position, Side
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


def test_halt_switch_blocks_plan() -> None:
    engine = RiskEngine(RiskConfig())
    signal = Signal(
        symbol="BTC/USDT",
        action=SignalAction.LONG,
        confidence=0.9,
        rationale=[],
        stop_loss=90,
        take_profit=120,
        last_price=100,
        market_type=MarketType.SPOT,
    )
    assert engine.build_plan(signal, RiskState(equity=1000, trading_halted=True)) is None


def test_symbol_exposure_limit_rejects_plan() -> None:
    engine = RiskEngine(RiskConfig(max_symbol_notional=100, max_notional_per_trade=100))
    plan_signal = Signal(
        symbol="BTC/USDT",
        action=SignalAction.LONG,
        confidence=0.9,
        rationale=[],
        stop_loss=90,
        take_profit=120,
        last_price=100,
        market_type=MarketType.SPOT,
    )
    state = RiskState(
        equity=10_000,
        open_positions=[
            Position(
                symbol="BTC/USDT",
                side=Side.BUY,
                amount=1,
                entry_price=90,
                mark_price=90,
            )
        ],
    )
    assert engine.build_plan(plan_signal, state) is None
