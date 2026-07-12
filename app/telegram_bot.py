from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import Settings
from app.core.execution import ApprovalBook, ExecutionEngine
from app.core.models import ExecutionResult
from app.core.risk import RiskConfig, RiskEngine, RiskState
from app.core.strategy import MultiFactorStrategy
from app.exchanges.base import Exchange
from app.exchanges.bitget import BitgetExchange
from app.exchanges.paper import PaperExchange


def build_application(settings: Settings) -> Application:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required")

    exchange: Exchange
    if settings.live_enabled:
        missing = [
            name
            for name, value in {
                "BITGET_API_KEY": settings.bitget_api_key,
                "BITGET_API_SECRET": settings.bitget_api_secret,
                "BITGET_API_PASSWORD": settings.bitget_api_password,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Live trading requested but missing: {', '.join(missing)}")
        exchange = BitgetExchange(
            settings.bitget_api_key or "",
            settings.bitget_api_secret or "",
            settings.bitget_api_password or "",
            settings.bitget_sandbox,
        )
    else:
        exchange = PaperExchange()

    approval_book = ApprovalBook()
    risk_engine = RiskEngine(
        RiskConfig(
            max_leverage=settings.max_leverage,
            default_risk_per_trade=settings.default_risk_per_trade,
            max_notional_per_trade=settings.max_notional_per_trade,
            max_daily_loss=settings.max_daily_loss,
        )
    )
    execution_engine = ExecutionEngine(exchange, approval_book, settings.approval_required)
    strategy = MultiFactorStrategy()

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings
    app.bot_data["exchange"] = exchange
    app.bot_data["approval_book"] = approval_book
    app.bot_data["risk_engine"] = risk_engine
    app.bot_data["execution_engine"] = execution_engine
    app.bot_data["strategy"] = strategy

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    return app


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    await update.effective_message.reply_text(
        "MyTradingAgent is online. Use /status, /scan SYMBOL, /pending, /approve ID, /reject ID."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    settings: Settings = context.bot_data["settings"]
    approval_book: ApprovalBook = context.bot_data["approval_book"]
    await update.effective_message.reply_text(
        "\n".join(
            [
                f"Mode: {settings.trading_mode}",
                f"Approval required: {settings.approval_required}",
                f"Max leverage: {settings.max_leverage}x",
                f"Pending approvals: {len(approval_book.pending)}",
            ]
        )
    )


async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /scan BTC/USDT")
        return

    symbol = context.args[0].upper()
    exchange: Exchange = context.bot_data["exchange"]
    strategy: MultiFactorStrategy = context.bot_data["strategy"]
    risk_engine: RiskEngine = context.bot_data["risk_engine"]
    execution_engine: ExecutionEngine = context.bot_data["execution_engine"]

    candles = await exchange.fetch_ohlcv(symbol)
    market_type = await exchange.market_type(symbol)
    signal = strategy.analyze(symbol, candles, market_type)
    equity = await exchange.equity()
    plan = risk_engine.build_plan(signal, RiskState(equity=equity))

    if plan is None:
        await update.effective_message.reply_text(
            "No trade plan.\n" + "\n".join(signal.rationale)
        )
        return

    errors = risk_engine.validate_plan(plan)
    if errors:
        await update.effective_message.reply_text("Risk rejected plan: " + "; ".join(errors))
        return

    result = await execution_engine.submit(plan)
    if isinstance(result, str):
        await update.effective_message.reply_text(_format_plan(plan=result, text_plan=plan))
    else:
        await update.effective_message.reply_text(_format_execution(result))


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    approval_book: ApprovalBook = context.bot_data["approval_book"]
    if not approval_book.pending:
        await update.effective_message.reply_text("No pending approvals.")
        return
    lines = []
    for approval_id, plan in approval_book.pending.items():
        lines.append(
            f"{approval_id}: {plan.side.value.upper()} {plan.amount} {plan.symbol} "
            f"notional={plan.notional:.2f} lev={plan.leverage}x"
        )
    await update.effective_message.reply_text("\n".join(lines))


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /approve <id>")
        return
    execution_engine: ExecutionEngine = context.bot_data["execution_engine"]
    result = await execution_engine.approve(context.args[0])
    if result is None:
        await update.effective_message.reply_text("Approval id not found.")
    else:
        await update.effective_message.reply_text(_format_execution(result))


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /reject <id>")
        return
    approval_book: ApprovalBook = context.bot_data["approval_book"]
    if approval_book.reject(context.args[0]):
        await update.effective_message.reply_text("Rejected.")
    else:
        await update.effective_message.reply_text("Approval id not found.")


async def _authorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    settings: Settings = context.bot_data["settings"]
    user = update.effective_user
    if not settings.telegram_allowed_user_ids:
        await update.effective_message.reply_text(
            "No TELEGRAM_ALLOWED_USER_IDS configured. Refusing commands."
        )
        return False
    if user is None or user.id not in settings.telegram_allowed_user_ids:
        await update.effective_message.reply_text("Unauthorized.")
        return False
    return True


def _format_plan(plan: str, text_plan) -> str:
    return "\n".join(
        [
            "Trade approval required.",
            f"Approval ID: {plan}",
            f"Symbol: {text_plan.symbol}",
            f"Side: {text_plan.side.value.upper()}",
            f"Amount: {text_plan.amount}",
            f"Entry: {text_plan.entry_price:.6f}",
            f"Notional: {text_plan.notional:.2f}",
            f"Leverage: {text_plan.leverage}x",
            f"Stop loss: {text_plan.stop_loss}",
            f"Take profit: {text_plan.take_profit}",
            "Rationale:",
            *[f"- {item}" for item in text_plan.rationale],
            f"Approve with /approve {plan}",
        ]
    )


def _format_execution(result: ExecutionResult) -> str:
    return "\n".join(
        [
            f"Order result: {'OK' if result.ok else 'FAILED'}",
            f"Mode: {result.mode}",
            f"Symbol: {result.symbol}",
            f"Side: {result.side.value}",
            f"Amount: {result.amount}",
            f"Order ID: {result.order_id}",
            f"Message: {result.message}",
        ]
    )
