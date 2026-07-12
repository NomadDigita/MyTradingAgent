from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.config import Settings
from app.core.alpha import AlphaConfluenceEngine
from app.core.attestation import AuditHashChain
from app.core.audit import AuditJournal
from app.core.backtest import LightweightBacktester
from app.core.execution import ApprovalBook, ExecutionEngine
from app.core.models import ExecutionResult
from app.core.portfolio import PortfolioSnapshot
from app.core.research import InstitutionalResearchEngine
from app.core.risk import RiskConfig, RiskEngine, RiskState
from app.core.scanner import MarketScanner
from app.core.sentinel import BlackSwanSentinel
from app.core.strategy import MultiFactorStrategy
from app.core.universe import resolve_universe, universe_menu
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

    audit = AuditJournal(settings.audit_log_path)
    approval_book = ApprovalBook(expiry_minutes=settings.approval_expiry_minutes)
    risk_engine = RiskEngine(
        RiskConfig(
            max_leverage=settings.max_leverage,
            default_risk_per_trade=settings.default_risk_per_trade,
            max_notional_per_trade=settings.max_notional_per_trade,
            max_daily_loss=settings.max_daily_loss,
            max_open_positions=settings.max_open_positions,
            max_symbol_notional=settings.max_symbol_notional,
            max_portfolio_notional=settings.max_portfolio_notional,
            min_signal_confidence=settings.min_signal_confidence,
            require_stop_loss=settings.require_stop_loss,
        )
    )
    execution_engine = ExecutionEngine(exchange, approval_book, settings.approval_required, audit)
    strategy = MultiFactorStrategy()
    research = InstitutionalResearchEngine()
    scanner = MarketScanner(exchange, research)
    alpha = AlphaConfluenceEngine()
    sentinel = BlackSwanSentinel()
    backtester = LightweightBacktester(alpha)
    hash_chain = AuditHashChain()

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.bot_data["settings"] = settings
    app.bot_data["exchange"] = exchange
    app.bot_data["audit"] = audit
    app.bot_data["approval_book"] = approval_book
    app.bot_data["risk_engine"] = risk_engine
    app.bot_data["execution_engine"] = execution_engine
    app.bot_data["strategy"] = strategy
    app.bot_data["research"] = research
    app.bot_data["scanner"] = scanner
    app.bot_data["alpha"] = alpha
    app.bot_data["sentinel"] = sentinel
    app.bot_data["backtester"] = backtester
    app.bot_data["hash_chain"] = hash_chain
    app.bot_data["trading_halted"] = False

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("scan", scan))
    app.add_handler(CommandHandler("research", research_command))
    app.add_handler(CommandHandler("alpha", alpha_command))
    app.add_handler(CommandHandler("sentinel", sentinel_command))
    app.add_handler(CommandHandler("backtest", backtest_command))
    app.add_handler(CommandHandler("scan_many", scan_many))
    app.add_handler(CommandHandler("universe", universe_command))
    app.add_handler(CommandHandler("audit_root", audit_root))
    app.add_handler(CommandHandler("portfolio", portfolio))
    app.add_handler(CommandHandler("risk", risk))
    app.add_handler(CommandHandler("halt", halt))
    app.add_handler(CommandHandler("resume", resume))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    return app


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    await update.effective_message.reply_text(
        "\n".join(
            [
                "MyTradingAgent institutional command center is online.",
                "",
                "Core:",
                "/status - operating mode and pending approvals",
                "/research SYMBOL - detailed research report",
                "/alpha SYMBOL - confluence alpha card",
                "/sentinel SYMBOL - black-swan anomaly check",
                "/backtest SYMBOL - lightweight walk-forward sanity test",
                "/scan SYMBOL - create a risk-checked approval plan",
                "/scan_many SYMBOL1 SYMBOL2 - rank symbols or a named universe",
                "/universe - list named universes",
                "/audit_root - tamper-evident audit hash root",
                "/portfolio - exposure and open positions",
                "/risk - active limits and kill-switch state",
                "/pending - pending approvals",
                "/approve ID - approve and execute",
                "/reject ID - reject approval",
                "/halt - activate operator kill switch",
                "/resume - deactivate operator kill switch",
            ]
        )
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    settings: Settings = context.bot_data["settings"]
    approval_book: ApprovalBook = context.bot_data["approval_book"]
    expired = approval_book.prune_expired()
    await update.effective_message.reply_text(
        "\n".join(
            [
                f"Mode: {settings.trading_mode}",
                f"Approval required: {settings.approval_required}",
                f"Max leverage: {settings.max_leverage}x",
                f"Trading halted: {context.bot_data['trading_halted']}",
                f"Pending approvals: {len(approval_book.pending)}",
                f"Expired approvals pruned: {len(expired)}",
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
    alpha: AlphaConfluenceEngine = context.bot_data["alpha"]
    sentinel: BlackSwanSentinel = context.bot_data["sentinel"]

    candles = await exchange.fetch_ohlcv(symbol)
    alpha_card = alpha.card(symbol, candles)
    if not alpha_card.data_quality.valid:
        await update.effective_message.reply_text(
            "Data-quality gate rejected scan.\n" + "\n".join(alpha_card.data_quality.issues)
        )
        return
    alert = sentinel.evaluate(symbol, candles)
    if alert.halt_recommended:
        context.bot_data["trading_halted"] = True
        audit: AuditJournal = context.bot_data["audit"]
        audit.record("sentinel_auto_halt", {"symbol": symbol, "alert": alert})
        await update.effective_message.reply_text(_format_sentinel(alert))
        return

    market_type = await exchange.market_type(symbol)
    signal = strategy.analyze(symbol, candles, market_type)
    state = await _risk_state(context)
    plan = risk_engine.build_plan(signal, state)

    if plan is None:
        await update.effective_message.reply_text(
            "No trade plan.\n" + "\n".join(signal.rationale)
        )
        return

    errors = risk_engine.validate_plan(plan, state)
    if errors:
        await update.effective_message.reply_text("Risk rejected plan: " + "; ".join(errors))
        return

    result = await execution_engine.submit(plan)
    if isinstance(result, str):
        await update.effective_message.reply_text(_format_plan(plan=result, text_plan=plan))
    else:
        await update.effective_message.reply_text(_format_execution(result))


async def research_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /research BTC/USDT")
        return
    symbol = context.args[0].upper()
    exchange: Exchange = context.bot_data["exchange"]
    research_engine: InstitutionalResearchEngine = context.bot_data["research"]
    candles = await exchange.fetch_ohlcv(symbol)
    market_type = await exchange.market_type(symbol)
    report = research_engine.report(symbol, candles, market_type)
    await update.effective_message.reply_text(_format_report(report))


async def scan_many(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    settings: Settings = context.bot_data["settings"]
    symbols = resolve_universe(context.args) if context.args else settings.default_scan_symbols
    scanner: MarketScanner = context.bot_data["scanner"]
    reports = await scanner.scan(symbols)
    lines = ["Market scanner ranking:"]
    for index, report in enumerate(reports[:10], start=1):
        lines.append(
            f"{index}. {report.symbol} score={report.score:.3f} action={report.action.value} "
            f"confidence={report.confidence:.3f} regime={report.regime.value}"
        )
    await update.effective_message.reply_text("\n".join(lines))


async def alpha_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /alpha BTC/USDT")
        return
    symbol = context.args[0].upper()
    exchange: Exchange = context.bot_data["exchange"]
    alpha: AlphaConfluenceEngine = context.bot_data["alpha"]
    candles = await exchange.fetch_ohlcv(symbol)
    card = alpha.card(symbol, candles)
    await update.effective_message.reply_text(_format_alpha(card))


async def sentinel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /sentinel BTC/USDT")
        return
    symbol = context.args[0].upper()
    exchange: Exchange = context.bot_data["exchange"]
    sentinel: BlackSwanSentinel = context.bot_data["sentinel"]
    candles = await exchange.fetch_ohlcv(symbol)
    alert = sentinel.evaluate(symbol, candles)
    if alert.halt_recommended:
        context.bot_data["trading_halted"] = True
        audit: AuditJournal = context.bot_data["audit"]
        audit.record("sentinel_auto_halt", {"symbol": symbol, "alert": alert})
    await update.effective_message.reply_text(_format_sentinel(alert))


async def backtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /backtest BTC/USDT")
        return
    symbol = context.args[0].upper()
    exchange: Exchange = context.bot_data["exchange"]
    backtester: LightweightBacktester = context.bot_data["backtester"]
    candles = await exchange.fetch_ohlcv(symbol, limit=240)
    metrics = backtester.run(symbol, candles)
    await update.effective_message.reply_text(
        "\n".join(
            [
                f"Backtest sanity check: {metrics.symbol}",
                f"Trades: {metrics.trades}",
                f"Win rate: {metrics.win_rate:.2%}",
                f"Total return: {metrics.total_return:.2%}",
                f"Max drawdown: {metrics.max_drawdown:.2%}",
                f"Profit factor: {metrics.profit_factor:.3f}",
                f"Expectancy: {metrics.expectancy:.5f}",
                f"Sharpe-like: {metrics.sharpe_like:.3f}",
                "Use this as a diagnostic only, not proof of future profitability.",
            ]
        )
    )


async def universe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    await update.effective_message.reply_text("Available universes:\n" + universe_menu())


async def audit_root(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    settings: Settings = context.bot_data["settings"]
    hash_chain: AuditHashChain = context.bot_data["hash_chain"]
    root = hash_chain.root(settings.audit_log_path)
    valid = hash_chain.verify_jsonl(settings.audit_log_path)
    await update.effective_message.reply_text(
        "\n".join(
            [
                "Audit attestation:",
                f"JSONL valid: {valid}",
                f"Hash root: {root}",
            ]
        )
    )


async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    exchange: Exchange = context.bot_data["exchange"]
    snapshot = PortfolioSnapshot(await exchange.equity(), await exchange.open_positions())
    lines = ["Portfolio snapshot:", *snapshot.risk_summary()]
    if snapshot.positions:
        lines.append("")
        lines.append("Positions:")
        for position in snapshot.positions[:20]:
            lines.append(
                f"- {position.symbol} {position.side.value} amount={position.amount:.8f} "
                f"notional={position.notional:.2f} lev={position.leverage}x"
            )
    await update.effective_message.reply_text("\n".join(lines))


async def risk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    risk_engine: RiskEngine = context.bot_data["risk_engine"]
    config = risk_engine.config
    await update.effective_message.reply_text(
        "\n".join(
            [
                "Risk limits:",
                f"Trading halted: {context.bot_data['trading_halted']}",
                f"Max leverage: {config.max_leverage}x",
                f"Min signal confidence: {config.min_signal_confidence}",
                f"Risk per trade: {config.default_risk_per_trade}",
                f"Max notional per trade: {config.max_notional_per_trade}",
                f"Max symbol notional: {config.max_symbol_notional}",
                f"Max portfolio notional: {config.max_portfolio_notional}",
                f"Max open positions: {config.max_open_positions}",
                f"Max daily loss: {config.max_daily_loss}",
                f"Require stop loss: {config.require_stop_loss}",
            ]
        )
    )


async def halt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    context.bot_data["trading_halted"] = True
    audit: AuditJournal = context.bot_data["audit"]
    audit.record("operator_halt", {"user_id": update.effective_user.id if update.effective_user else None})
    await update.effective_message.reply_text("Operator kill switch activated. New trade plans are blocked.")


async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _authorized(update, context):
        return
    context.bot_data["trading_halted"] = False
    audit: AuditJournal = context.bot_data["audit"]
    audit.record("operator_resume", {"user_id": update.effective_user.id if update.effective_user else None})
    await update.effective_message.reply_text("Operator kill switch cleared. Risk checks remain active.")


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
    execution_engine: ExecutionEngine = context.bot_data["execution_engine"]
    if execution_engine.reject(context.args[0]):
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


async def _risk_state(context: ContextTypes.DEFAULT_TYPE) -> RiskState:
    exchange: Exchange = context.bot_data["exchange"]
    return RiskState(
        equity=await exchange.equity(),
        realized_pnl_today=0.0,
        open_positions=await exchange.open_positions(),
        trading_halted=bool(context.bot_data["trading_halted"]),
    )


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
            f"Approval expires in configured window.",
            "Rationale:",
            *[f"- {item}" for item in text_plan.rationale],
            f"Approve with /approve {plan}",
        ]
    )


def _format_report(report) -> str:
    return "\n".join(
        [
            f"Research report: {report.symbol}",
            f"Action: {report.action.value}",
            f"Score: {report.score:.3f}",
            f"Confidence: {report.confidence:.3f}",
            f"Regime: {report.regime.value}",
            f"Last price: {report.last_price:.6f}",
            f"Realized volatility: {report.volatility:.4f}",
            "",
            "Risk notes:",
            *[f"- {item}" for item in report.risk_notes],
            "",
            "Rationale:",
            *[f"- {item}" for item in report.rationale[:10]],
        ]
    )


def _format_alpha(card) -> str:
    lines = [
        f"Alpha confluence card: {card.symbol}",
        f"Action: {card.action.value}",
        f"Score: {card.score:.4f}",
        f"Confidence: {card.confidence:.4f}",
        f"Data quality: {card.data_quality.score:.3f} valid={card.data_quality.valid}",
        "",
        "Data quality notes:",
        *[f"- {item}" for item in card.data_quality.issues],
    ]
    if card.votes:
        lines.extend(["", "Votes:"])
        for vote in card.votes:
            lines.append(
                f"- {vote.name}: direction={vote.direction:.2f} "
                f"confidence={vote.confidence:.2f}; {vote.reason}"
            )
    return "\n".join(lines)


def _format_sentinel(alert) -> str:
    return "\n".join(
        [
            f"Black-swan sentinel: {alert.symbol}",
            f"Level: {alert.level.value}",
            f"Severity: {alert.severity:.3f}",
            f"Halt recommended: {alert.halt_recommended}",
            "Triggers:",
            *[f"- {item}" for item in alert.triggers],
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
