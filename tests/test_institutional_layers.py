from pathlib import Path

from app.core.alpha import AlphaConfluenceEngine
from app.core.attestation import AuditHashChain
from app.core.data_quality import DataQualityGate
from app.core.models import Candle
from app.core.sentinel import BlackSwanSentinel


def _candles(count: int = 100) -> list[Candle]:
    price = 100.0
    rows: list[Candle] = []
    for index in range(count):
        price *= 1.001
        rows.append(
            Candle(
                timestamp=index * 60_000,
                open=price * 0.999,
                high=price * 1.002,
                low=price * 0.998,
                close=price,
                volume=1000 + index,
            )
        )
    return rows


def test_data_quality_rejects_invalid_ohlc() -> None:
    rows = _candles()
    rows[10] = Candle(600_000, 100, 90, 110, 100, 1000)
    report = DataQualityGate().evaluate("BTC/USDT", rows)
    assert not report.valid
    assert any("invalid OHLC" in issue for issue in report.issues)


def test_alpha_card_has_votes_for_clean_data() -> None:
    card = AlphaConfluenceEngine().card("BTC/USDT", _candles())
    assert card.data_quality.valid
    assert len(card.votes) == 5


def test_sentinel_recommends_halt_on_shock() -> None:
    rows = _candles()
    rows[-1] = Candle(rows[-1].timestamp, 100, 150, 80, 140, 10_000)
    alert = BlackSwanSentinel().evaluate("BTC/USDT", rows)
    assert alert.severity >= 0.55
    assert alert.level.value in {"warning", "critical"}


def test_audit_hash_chain_validates_jsonl(tmp_path: Path) -> None:
    audit = tmp_path / "audit.jsonl"
    audit.write_text('{"event_type":"test"}\n{"event_type":"test2"}\n', encoding="utf-8")
    chain = AuditHashChain()
    assert chain.verify_jsonl(str(audit))
    assert len(chain.root(str(audit))) == 64
