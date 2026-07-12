from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_allowed_user_ids: set[int]
    trading_mode: str
    approval_required: bool
    max_leverage: float
    default_risk_per_trade: float
    max_notional_per_trade: float
    max_daily_loss: float
    max_open_positions: int
    max_symbol_notional: float
    max_portfolio_notional: float
    min_signal_confidence: float
    require_stop_loss: bool
    approval_expiry_minutes: int
    default_scan_symbols: list[str]
    audit_log_path: str
    bitget_api_key: str | None
    bitget_api_secret: str | None
    bitget_api_password: str | None
    bitget_sandbox: bool
    database_url: str
    risk_service_url: str | None
    log_level: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        allowed = {
            int(item.strip())
            for item in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",")
            if item.strip().isdigit()
        }
        max_leverage = min(float(os.getenv("MAX_LEVERAGE", "20")), 20.0)
        mode = os.getenv("TRADING_MODE", "paper").strip().lower()
        if mode not in {"paper", "live"}:
            mode = "paper"
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_allowed_user_ids=allowed,
            trading_mode=mode,
            approval_required=_bool("APPROVAL_REQUIRED", True),
            max_leverage=max_leverage,
            default_risk_per_trade=float(os.getenv("DEFAULT_RISK_PER_TRADE", "0.005")),
            max_notional_per_trade=float(os.getenv("MAX_NOTIONAL_PER_TRADE", "100")),
            max_daily_loss=float(os.getenv("MAX_DAILY_LOSS", "50")),
            max_open_positions=int(os.getenv("MAX_OPEN_POSITIONS", "5")),
            max_symbol_notional=float(os.getenv("MAX_SYMBOL_NOTIONAL", "250")),
            max_portfolio_notional=float(os.getenv("MAX_PORTFOLIO_NOTIONAL", "500")),
            min_signal_confidence=float(os.getenv("MIN_SIGNAL_CONFIDENCE", "0.55")),
            require_stop_loss=_bool("REQUIRE_STOP_LOSS", True),
            approval_expiry_minutes=int(os.getenv("APPROVAL_EXPIRY_MINUTES", "15")),
            default_scan_symbols=_csv("DEFAULT_SCAN_SYMBOLS", ["BTC/USDT", "ETH/USDT", "SOL/USDT"]),
            audit_log_path=os.getenv("AUDIT_LOG_PATH", "logs/audit.jsonl"),
            bitget_api_key=os.getenv("BITGET_API_KEY") or None,
            bitget_api_secret=os.getenv("BITGET_API_SECRET") or None,
            bitget_api_password=os.getenv("BITGET_API_PASSWORD") or None,
            bitget_sandbox=_bool("BITGET_SANDBOX", False),
            database_url=os.getenv("DATABASE_URL", "sqlite:///data/trading_agent.sqlite"),
            risk_service_url=os.getenv("RISK_SERVICE_URL") or None,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

    @property
    def live_enabled(self) -> bool:
        return self.trading_mode == "live"


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _csv(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip().upper() for item in value.split(",") if item.strip()]
